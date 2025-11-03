"""
ViewSet para gestión de avatares del sistema.

Proporciona endpoints para:
- Listar avatares disponibles
- Ver detalles de un avatar
- Obtener avatares según el rol del usuario
- CRUD completo (admin only para create/update/delete)
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from src.infrastructure.security.temp_disable_auth import DisableAuthenticationMixin
from src.adapters.secondary.database.models import Avatar
from src.adapters.primary.rest_api.serializers import AvatarSerializer



@extend_schema_view(
    list=extend_schema(
        summary="Listar avatares",
        description="Obtiene lista de avatares disponibles. Admite filtrado por rol.",
        tags=["Avatares"]
    ),
    retrieve=extend_schema(
        summary="Detalle de avatar",
        description="Obtiene los detalles de un avatar específico.",
        tags=["Avatares"]
    ),
    create=extend_schema(
        summary="Crear avatar",
        description="Crea un nuevo avatar (solo administradores).",
        tags=["Avatares"]
    ),
    update=extend_schema(
        summary="Actualizar avatar",
        description="Actualiza un avatar existente (solo administradores).",
        tags=["Avatares"]
    ),
    partial_update=extend_schema(
        summary="Actualización parcial de avatar",
        description="Actualiza parcialmente un avatar (solo administradores).",
        tags=["Avatares"]
    ),
    destroy=extend_schema(
        summary="Eliminar avatar",
        description="Elimina un avatar del sistema (solo administradores).",
        tags=["Avatares"]
    ),
)
class AvatarViewSet(DisableAuthenticationMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de avatares.
    
    Endpoints disponibles:
    - GET /api/avatars/ - Lista de avatares
    - GET /api/avatars/{id}/ - Detalle de avatar
    - GET /api/avatars/my-role-avatars/ - Avatares del rol del usuario actual
    - GET /api/avatars/by-role/?role=PRACTICANTE - Filtrar por rol
    - POST /api/avatars/ - Crear avatar (admin only)
    - PUT/PATCH /api/avatars/{id}/ - Actualizar (admin only)
    - DELETE /api/avatars/{id}/ - Eliminar (admin only)
    """
    
    queryset = Avatar.objects.filter(is_active=True).order_by('role', '-created_at')
    serializer_class = AvatarSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """
        Permisos personalizados según la acción.
        
        - list, retrieve, my_role_avatars, by_role: Cualquier usuario autenticado
        - create, update, partial_update, destroy: Solo administradores
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """
        Filtra el queryset según parámetros.
        
        Soporta filtrado por:
        - role: Filtra avatares de un rol específico
        - is_active: Muestra avatares activos/inactivos (admin only)
        """
        queryset = super().get_queryset()
        
        # Filtrar por rol si se proporciona
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role.upper())
        
        # Solo admins pueden ver avatares inactivos
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    @extend_schema(
        summary="Avatares del rol del usuario",
        description="Retorna los avatares disponibles para el rol del usuario autenticado.",
        tags=["Avatares"],
        responses={200: AvatarSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_role_avatars(self, request):
        """
        Obtiene avatares del rol del usuario actual.
        
        Returns:
            Response con lista de avatares del rol del usuario.
        """
        user_role = request.user.role
        
        avatars = Avatar.objects.filter(
            role=user_role,
            is_active=True
        ).order_by('-created_at')
        
        serializer = self.get_serializer(avatars, many=True)
        
        return Response({
            'count': avatars.count(),
            'role': user_role,
            'avatars': serializer.data
        })
    
    @extend_schema(
        summary="Avatares por rol",
        description="Filtra avatares por un rol específico.",
        tags=["Avatares"],
        parameters=[
            OpenApiParameter(
                name='role',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Rol a filtrar (PRACTICANTE, SUPERVISOR, COORDINADOR, etc.)',
                required=True,
                enum=['PRACTICANTE', 'SUPERVISOR', 'COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']
            )
        ],
        responses={200: AvatarSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def by_role(self, request):
        """
        Filtra avatares por rol específico.
        
        Query params:
            role (str): Rol a filtrar
        
        Returns:
            Response con lista de avatares del rol especificado.
        """
        role = request.query_params.get('role', '').upper()
        
        if not role:
            return Response(
                {'error': 'Parámetro "role" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        valid_roles = ['PRACTICANTE', 'SUPERVISOR', 'COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']
        if role not in valid_roles:
            return Response(
                {
                    'error': f'Rol inválido. Opciones: {", ".join(valid_roles)}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        avatars = Avatar.objects.filter(
            role=role,
            is_active=True
        ).order_by('-created_at')
        
        serializer = self.get_serializer(avatars, many=True)
        
        return Response({
            'count': avatars.count(),
            'role': role,
            'avatars': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """Crear nuevo avatar (admin only)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(
            {
                'message': 'Avatar creado exitosamente',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Actualizar avatar (admin only)."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'message': 'Avatar actualizado exitosamente',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar avatar (soft delete - marca como inactivo)."""
        instance = self.get_object()
        
        # Soft delete - solo marcar como inactivo
        instance.is_active = False
        instance.save()
        
        return Response(
            {'message': 'Avatar eliminado exitosamente'},
            status=status.HTTP_204_NO_CONTENT
        )
