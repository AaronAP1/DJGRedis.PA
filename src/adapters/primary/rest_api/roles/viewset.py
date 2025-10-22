"""
ViewSet para gestión de roles del sistema RBAC.

Proporciona endpoints para:
- CRUD completo de roles
- Asignar/remover permisos a roles
- Listar usuarios con un rol específico
- Obtener permisos de un rol
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db.models import Count
from django.contrib.auth import get_user_model

from src.adapters.secondary.database.models import Role, Permission, RolePermission
from src.adapters.primary.rest_api.serializers import (
    RoleSerializer, RoleListSerializer, RoleCreateSerializer,
    PermissionSerializer, RolePermissionSerializer
)

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="Listar roles",
        description="Obtiene lista de roles del sistema. Usuarios autenticados pueden ver, solo admins pueden modificar.",
        tags=["Roles y Permisos"]
    ),
    retrieve=extend_schema(
        summary="Detalle de rol",
        description="Obtiene los detalles de un rol específico con sus permisos.",
        tags=["Roles y Permisos"]
    ),
    create=extend_schema(
        summary="Crear rol",
        description="Crea un nuevo rol en el sistema (solo administradores).",
        tags=["Roles y Permisos"]
    ),
    update=extend_schema(
        summary="Actualizar rol",
        description="Actualiza un rol existente (solo administradores).",
        tags=["Roles y Permisos"]
    ),
    partial_update=extend_schema(
        summary="Actualización parcial de rol",
        description="Actualiza parcialmente un rol (solo administradores).",
        tags=["Roles y Permisos"]
    ),
    destroy=extend_schema(
        summary="Eliminar rol",
        description="Desactiva un rol del sistema (solo administradores, no elimina roles del sistema).",
        tags=["Roles y Permisos"]
    ),
)
class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de roles RBAC.
    
    Endpoints disponibles:
    - GET /api/v2/roles/ - Lista de roles
    - GET /api/v2/roles/{id}/ - Detalle de rol con permisos
    - GET /api/v2/roles/{id}/permissions/ - Permisos del rol
    - GET /api/v2/roles/{id}/users/ - Usuarios con este rol
    - POST /api/v2/roles/ - Crear rol (admin only)
    - POST /api/v2/roles/{id}/add-permission/ - Agregar permiso (admin only)
    - DELETE /api/v2/roles/{id}/remove-permission/ - Remover permiso (admin only)
    - PUT/PATCH /api/v2/roles/{id}/ - Actualizar (admin only)
    - DELETE /api/v2/roles/{id}/ - Desactivar (admin only)
    """
    
    queryset = Role.objects.all().prefetch_related('permissions').order_by('code')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción."""
        if self.action == 'list':
            return RoleListSerializer
        elif self.action == 'create':
            return RoleCreateSerializer
        return RoleSerializer
    
    def get_permissions(self):
        """
        Permisos personalizados según la acción.
        
        - list, retrieve: Cualquier usuario autenticado
        - create, update, partial_update, destroy, add/remove permissions: Solo administradores
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy', 
                          'add_permission', 'remove_permission']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """
        Filtra el queryset según parámetros.
        
        Soporta filtrado por:
        - is_active: Muestra roles activos/inactivos
        - is_system: Filtra roles del sistema
        """
        queryset = super().get_queryset()
        
        # Filtrar por estado activo
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filtrar roles del sistema
        is_system = self.request.query_params.get('is_system', None)
        if is_system is not None:
            queryset = queryset.filter(is_system=is_system.lower() == 'true')
        
        return queryset
    
    @extend_schema(
        summary="Permisos del rol",
        description="Retorna todos los permisos asignados a un rol específico.",
        tags=["Roles y Permisos"],
        responses={200: PermissionSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def permissions(self, request, pk=None):
        """
        Obtiene los permisos de un rol.
        
        Returns:
            Response con lista de permisos del rol.
        """
        role = self.get_object()
        permissions = role.permissions.filter(is_active=True).order_by('module', 'code')
        
        serializer = PermissionSerializer(permissions, many=True)
        
        return Response({
            'role': {
                'id': role.id,
                'code': role.code,
                'name': role.name
            },
            'permissions_count': permissions.count(),
            'permissions': serializer.data
        })
    
    @extend_schema(
        summary="Usuarios con este rol",
        description="Retorna todos los usuarios que tienen asignado este rol.",
        tags=["Roles y Permisos"],
        parameters=[
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filtrar solo usuarios activos',
                required=False
            )
        ]
    )
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def users(self, request, pk=None):
        """
        Obtiene usuarios con este rol.
        
        Query params:
            is_active (bool): Filtrar solo usuarios activos
        
        Returns:
            Response con lista de usuarios.
        """
        role = self.get_object()
        users = User.objects.filter(role=role.code)
        
        # Filtrar por estado activo si se proporciona
        is_active = request.query_params.get('is_active', None)
        if is_active is not None:
            users = users.filter(is_active=is_active.lower() == 'true')
        
        users_data = [
            {
                'id': user.id,
                'email': user.email,
                'full_name': user.get_full_name(),
                'is_active': user.is_active,
                'date_joined': user.date_joined
            }
            for user in users
        ]
        
        return Response({
            'role': {
                'id': role.id,
                'code': role.code,
                'name': role.name
            },
            'users_count': users.count(),
            'users': users_data
        })
    
    @extend_schema(
        summary="Agregar permiso a rol",
        description="Asigna un permiso específico a un rol (solo administradores).",
        tags=["Roles y Permisos"],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'permission_id': {'type': 'string', 'format': 'uuid'}
                },
                'required': ['permission_id']
            }
        },
        responses={200: RoleSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def add_permission(self, request, pk=None):
        """
        Agrega un permiso a un rol.
        
        Body:
            permission_id (UUID): ID del permiso a agregar
        
        Returns:
            Response con rol actualizado.
        """
        role = self.get_object()
        permission_id = request.data.get('permission_id')
        
        if not permission_id:
            return Response(
                {'error': 'Se requiere permission_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            permission = Permission.objects.get(id=permission_id, is_active=True)
        except Permission.DoesNotExist:
            return Response(
                {'error': 'Permiso no encontrado o inactivo'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar si ya tiene el permiso
        if role.permissions.filter(id=permission_id).exists():
            return Response(
                {'error': f'El rol ya tiene el permiso "{permission.code}"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Agregar permiso
        RolePermission.objects.create(
            role=role,
            permission=permission,
            granted_by=request.user
        )
        
        serializer = self.get_serializer(role)
        
        return Response({
            'message': f'Permiso "{permission.code}" agregado exitosamente al rol "{role.name}"',
            'data': serializer.data
        })
    
    @extend_schema(
        summary="Remover permiso de rol",
        description="Remueve un permiso específico de un rol (solo administradores).",
        tags=["Roles y Permisos"],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'permission_id': {'type': 'string', 'format': 'uuid'}
                },
                'required': ['permission_id']
            }
        },
        responses={200: RoleSerializer}
    )
    @action(detail=True, methods=['delete'], permission_classes=[IsAdminUser])
    def remove_permission(self, request, pk=None):
        """
        Remueve un permiso de un rol.
        
        Body:
            permission_id (UUID): ID del permiso a remover
        
        Returns:
            Response con rol actualizado.
        """
        role = self.get_object()
        permission_id = request.data.get('permission_id')
        
        if not permission_id:
            return Response(
                {'error': 'Se requiere permission_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            permission = Permission.objects.get(id=permission_id)
        except Permission.DoesNotExist:
            return Response(
                {'error': 'Permiso no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar si tiene el permiso
        if not role.permissions.filter(id=permission_id).exists():
            return Response(
                {'error': f'El rol no tiene el permiso "{permission.code}"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remover permiso
        role.permissions.remove(permission)
        
        serializer = self.get_serializer(role)
        
        return Response({
            'message': f'Permiso "{permission.code}" removido exitosamente del rol "{role.name}"',
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """Crear nuevo rol (admin only)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Retornar con serializer completo
        role = serializer.instance
        detail_serializer = RoleSerializer(role)
        
        return Response(
            {
                'message': 'Rol creado exitosamente',
                'data': detail_serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Actualizar rol (admin only)."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # No permitir modificar roles del sistema
        if instance.is_system:
            return Response(
                {'error': 'No se pueden modificar roles del sistema'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'message': 'Rol actualizado exitosamente',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Desactivar rol (soft delete - no elimina roles del sistema)."""
        instance = self.get_object()
        
        # No permitir eliminar roles del sistema
        if instance.is_system:
            return Response(
                {'error': 'No se pueden eliminar roles del sistema'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Soft delete - solo marcar como inactivo
        instance.is_active = False
        instance.save()
        
        return Response(
            {'message': f'Rol "{instance.name}" desactivado exitosamente'},
            status=status.HTTP_204_NO_CONTENT
        )
