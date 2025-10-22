"""
ViewSet para gestión de permisos específicos de usuario (overrides).

Proporciona endpoints para:
- Listar overrides de permisos
- Ver detalles de un override
- Otorgar permiso adicional a usuario (GRANT)
- Revocar permiso del rol a usuario (REVOKE)
- Eliminar override
- Ver overrides por usuario
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from src.adapters.secondary.database.models import UserPermission, Permission
from src.adapters.primary.rest_api.serializers import (
    UserPermissionSerializer, UserPermissionCreateSerializer
)

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="Listar permisos de usuario",
        description="Obtiene lista de overrides de permisos por usuario (solo administradores).",
        tags=["Permisos de Usuario"]
    ),
    retrieve=extend_schema(
        summary="Detalle de permiso de usuario",
        description="Obtiene los detalles de un override específico.",
        tags=["Permisos de Usuario"]
    ),
    create=extend_schema(
        summary="Otorgar/Revocar permiso a usuario",
        description="Crea un override de permiso para un usuario (GRANT o REVOKE, solo administradores).",
        tags=["Permisos de Usuario"]
    ),
    destroy=extend_schema(
        summary="Eliminar override de permiso",
        description="Elimina un override de permiso de usuario (solo administradores).",
        tags=["Permisos de Usuario"]
    ),
)
class UserPermissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de permisos específicos de usuario (overrides).
    
    Los overrides pueden ser:
    - GRANT: Otorga un permiso adicional que no tiene por su rol
    - REVOKE: Revoca un permiso que tiene por su rol
    
    Endpoints disponibles:
    - GET /api/v2/user-permissions/ - Lista de overrides (admin only)
    - GET /api/v2/user-permissions/{id}/ - Detalle de override
    - GET /api/v2/user-permissions/by-user/{user_id}/ - Overrides de un usuario
    - GET /api/v2/user-permissions/active/ - Solo overrides activos (no expirados)
    - POST /api/v2/user-permissions/ - Crear override (admin only)
    - DELETE /api/v2/user-permissions/{id}/ - Eliminar override (admin only)
    """
    
    queryset = UserPermission.objects.all().select_related(
        'user', 'permission', 'granted_by'
    ).order_by('-granted_at')
    permission_classes = [IsAdminUser]  # Solo admins pueden gestionar overrides
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción."""
        if self.action == 'create':
            return UserPermissionCreateSerializer
        return UserPermissionSerializer
    
    def get_queryset(self):
        """
        Filtra el queryset según parámetros.
        
        Soporta filtrado por:
        - user: Filtra por usuario específico
        - permission_type: GRANT o REVOKE
        - is_active: Solo permisos no expirados
        """
        queryset = super().get_queryset()
        
        # Filtrar por usuario
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filtrar por tipo
        permission_type = self.request.query_params.get('permission_type', None)
        if permission_type:
            queryset = queryset.filter(permission_type=permission_type.upper())
        
        # Filtrar solo activos (no expirados)
        is_active = self.request.query_params.get('is_active', None)
        if is_active and is_active.lower() == 'true':
            queryset = queryset.filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            )
        
        return queryset
    
    @extend_schema(
        summary="Permisos de un usuario específico",
        description="Retorna todos los overrides de permisos de un usuario.",
        tags=["Permisos de Usuario"],
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='ID del usuario',
                required=True
            ),
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filtrar solo permisos no expirados',
                required=False
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='by-user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """
        Obtiene overrides de permisos de un usuario específico.
        
        Path params:
            user_id (UUID): ID del usuario
        
        Query params:
            is_active (bool): Filtrar solo no expirados
        
        Returns:
            Response con lista de overrides del usuario.
        """
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        queryset = UserPermission.objects.filter(user=user).select_related(
            'permission', 'granted_by'
        )
        
        # Filtrar solo activos si se solicita
        is_active = request.query_params.get('is_active', None)
        if is_active and is_active.lower() == 'true':
            queryset = queryset.filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            )
        
        serializer = UserPermissionSerializer(queryset, many=True)
        
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.get_full_name(),
                'role': user.role
            },
            'overrides_count': queryset.count(),
            'overrides': serializer.data
        })
    
    @extend_schema(
        summary="Overrides activos",
        description="Retorna solo los overrides de permisos que no han expirado.",
        tags=["Permisos de Usuario"]
    )
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Obtiene solo overrides activos (no expirados).
        
        Returns:
            Response con lista de overrides activos.
        """
        queryset = self.get_queryset().filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )
        
        serializer = UserPermissionSerializer(queryset, many=True)
        
        return Response({
            'active_count': queryset.count(),
            'overrides': serializer.data
        })
    
    @extend_schema(
        summary="Overrides expirados",
        description="Retorna los overrides de permisos que ya expiraron.",
        tags=["Permisos de Usuario"]
    )
    @action(detail=False, methods=['get'])
    def expired(self, request):
        """
        Obtiene overrides expirados.
        
        Returns:
            Response con lista de overrides expirados.
        """
        queryset = self.get_queryset().filter(
            expires_at__isnull=False,
            expires_at__lte=timezone.now()
        )
        
        serializer = UserPermissionSerializer(queryset, many=True)
        
        return Response({
            'expired_count': queryset.count(),
            'overrides': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """
        Crear override de permiso (GRANT o REVOKE).
        
        Body:
            user (UUID): ID del usuario
            permission (UUID): ID del permiso
            permission_type (str): "GRANT" o "REVOKE"
            reason (str): Razón del override
            expires_at (datetime): Fecha de expiración (opcional)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Asignar el usuario que otorga el permiso
        user_permission = serializer.save(granted_by=request.user)
        
        # Retornar con serializer completo
        detail_serializer = UserPermissionSerializer(user_permission)
        
        permission_type_text = "otorgado" if user_permission.permission_type == "GRANT" else "revocado"
        
        return Response(
            {
                'message': f'Permiso "{user_permission.permission.code}" {permission_type_text} exitosamente',
                'data': detail_serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar override de permiso."""
        instance = self.get_object()
        
        permission_code = instance.permission.code
        user_email = instance.user.email
        
        instance.delete()
        
        return Response(
            {
                'message': f'Override de permiso "{permission_code}" eliminado para usuario {user_email}'
            },
            status=status.HTTP_204_NO_CONTENT
        )
