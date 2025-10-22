"""
ViewSet para gestión de permisos del sistema.

Proporciona endpoints para:
- Listar permisos disponibles
- Ver detalles de un permiso
- Crear nuevos permisos (admin only)
- Agrupar permisos por módulo
- Ver roles que tienen un permiso
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db.models import Count, Q

from src.adapters.secondary.database.models import Permission, Role
from src.adapters.primary.rest_api.serializers import (
    PermissionSerializer, PermissionListSerializer
)


@extend_schema_view(
    list=extend_schema(
        summary="Listar permisos",
        description="Obtiene lista de permisos del sistema. Todos los usuarios autenticados pueden ver.",
        tags=["Roles y Permisos"]
    ),
    retrieve=extend_schema(
        summary="Detalle de permiso",
        description="Obtiene los detalles de un permiso específico.",
        tags=["Roles y Permisos"]
    ),
    create=extend_schema(
        summary="Crear permiso",
        description="Crea un nuevo permiso en el sistema (solo administradores).",
        tags=["Roles y Permisos"]
    ),
    update=extend_schema(
        summary="Actualizar permiso",
        description="Actualiza un permiso existente (solo administradores).",
        tags=["Roles y Permisos"]
    ),
    partial_update=extend_schema(
        summary="Actualización parcial de permiso",
        description="Actualiza parcialmente un permiso (solo administradores).",
        tags=["Roles y Permisos"]
    ),
    destroy=extend_schema(
        summary="Desactivar permiso",
        description="Desactiva un permiso del sistema (solo administradores).",
        tags=["Roles y Permisos"]
    ),
)
class PermissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de permisos del sistema.
    
    Endpoints disponibles:
    - GET /api/v2/permissions/ - Lista de permisos
    - GET /api/v2/permissions/{id}/ - Detalle de permiso
    - GET /api/v2/permissions/by-module/ - Agrupar por módulo
    - GET /api/v2/permissions/{id}/roles/ - Roles con este permiso
    - POST /api/v2/permissions/ - Crear permiso (admin only)
    - PUT/PATCH /api/v2/permissions/{id}/ - Actualizar (admin only)
    - DELETE /api/v2/permissions/{id}/ - Desactivar (admin only)
    """
    
    queryset = Permission.objects.all().order_by('module', 'code')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción."""
        if self.action == 'list':
            return PermissionListSerializer
        return PermissionSerializer
    
    def get_permissions(self):
        """
        Permisos personalizados según la acción.
        
        - list, retrieve, by_module, roles: Cualquier usuario autenticado
        - create, update, partial_update, destroy: Solo administradores
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """
        Filtra el queryset según parámetros.
        
        Soporta filtrado por:
        - module: Filtra permisos de un módulo específico
        - is_active: Muestra permisos activos/inactivos
        - search: Busca en code, name o description
        """
        queryset = super().get_queryset()
        
        # Filtrar por módulo
        module = self.request.query_params.get('module', None)
        if module:
            queryset = queryset.filter(module__iexact=module)
        
        # Filtrar por estado activo
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Búsqueda en code, name, description
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset
    
    @extend_schema(
        summary="Permisos agrupados por módulo",
        description="Retorna los permisos agrupados por módulo del sistema.",
        tags=["Roles y Permisos"],
        parameters=[
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filtrar solo permisos activos',
                required=False
            )
        ]
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def by_module(self, request):
        """
        Agrupa permisos por módulo.
        
        Query params:
            is_active (bool): Filtrar solo permisos activos
        
        Returns:
            Response con permisos agrupados por módulo.
        """
        queryset = self.get_queryset()
        
        # Filtrar solo activos si se solicita
        is_active = request.query_params.get('is_active', 'true')
        if is_active.lower() == 'true':
            queryset = queryset.filter(is_active=True)
        
        # Agrupar por módulo
        modules = {}
        for permission in queryset:
            module = permission.module or 'general'
            if module not in modules:
                modules[module] = []
            
            modules[module].append({
                'id': permission.id,
                'code': permission.code,
                'name': permission.name,
                'description': permission.description,
                'is_active': permission.is_active
            })
        
        # Convertir a lista ordenada
        modules_list = [
            {
                'module': module,
                'permissions_count': len(permissions),
                'permissions': permissions
            }
            for module, permissions in sorted(modules.items())
        ]
        
        return Response({
            'modules_count': len(modules_list),
            'total_permissions': queryset.count(),
            'modules': modules_list
        })
    
    @extend_schema(
        summary="Roles con este permiso",
        description="Retorna todos los roles que tienen asignado este permiso.",
        tags=["Roles y Permisos"],
        parameters=[
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filtrar solo roles activos',
                required=False
            )
        ]
    )
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def roles(self, request, pk=None):
        """
        Obtiene roles que tienen este permiso.
        
        Query params:
            is_active (bool): Filtrar solo roles activos
        
        Returns:
            Response con lista de roles.
        """
        permission = self.get_object()
        roles = Role.objects.filter(permissions=permission)
        
        # Filtrar por estado activo si se proporciona
        is_active = request.query_params.get('is_active', None)
        if is_active is not None:
            roles = roles.filter(is_active=is_active.lower() == 'true')
        
        roles_data = [
            {
                'id': role.id,
                'code': role.code,
                'name': role.name,
                'is_active': role.is_active,
                'is_system': role.is_system
            }
            for role in roles
        ]
        
        return Response({
            'permission': {
                'id': permission.id,
                'code': permission.code,
                'name': permission.name
            },
            'roles_count': roles.count(),
            'roles': roles_data
        })
    
    def create(self, request, *args, **kwargs):
        """Crear nuevo permiso (admin only)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Convertir code a mayúsculas
        if 'code' in serializer.validated_data:
            serializer.validated_data['code'] = serializer.validated_data['code'].upper()
        
        self.perform_create(serializer)
        
        return Response(
            {
                'message': 'Permiso creado exitosamente',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Actualizar permiso (admin only)."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'message': 'Permiso actualizado exitosamente',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Desactivar permiso (soft delete)."""
        instance = self.get_object()
        
        # Soft delete - solo marcar como inactivo
        instance.is_active = False
        instance.save()
        
        return Response(
            {'message': f'Permiso "{instance.code}" desactivado exitosamente'},
            status=status.HTTP_204_NO_CONTENT
        )
