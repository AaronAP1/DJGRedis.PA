"""
ViewSets auxiliares para School y Company (endpoints de soporte).
"""

from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter

from src.adapters.secondary.database.models import School, Company
from rest_framework import serializers


# ============================================================================
# SERIALIZERS
# ============================================================================

class SchoolListSerializer(serializers.ModelSerializer):
    """Serializer simple para listado de escuelas."""
    
    class Meta:
        model = School
        fields = ['id', 'nombre', 'codigo', 'estado']


class CompanyListSerializer(serializers.ModelSerializer):
    """Serializer simple para listado de empresas."""
    
    class Meta:
        model = Company
        fields = [
            'id', 
            'nombre', 
            'ruc', 
            'razon_social',
            'direccion',
            'telefono',
            'correo',
            'sector_economico',
            'estado'
        ]


class CompanyCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear empresas desde carta de presentación."""
    
    class Meta:
        model = Company
        fields = [
            'id',
            'nombre',
            'ruc',
            'razon_social',
            'direccion',
            'distrito',
            'provincia',
            'departamento',
            'telefono',
            'correo',
            'sitio_web',
            'sector_economico',
            'tamaño_empresa',
        ]
    
    def validate_ruc(self, value):
        """Validar formato de RUC."""
        import re
        if not re.match(r'^\d{11}$', value):
            raise serializers.ValidationError('RUC debe tener exactamente 11 dígitos')
        
        # Verificar que no exista
        if Company.objects.filter(ruc=value).exists():
            raise serializers.ValidationError('Ya existe una empresa con este RUC')
        
        return value


# ============================================================================
# VIEWSETS
# ============================================================================

@extend_schema(tags=['Escuelas Profesionales'])
class SchoolViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para Escuelas Profesionales.
    
    Endpoints:
    - GET /api/v2/schools/ - Listar escuelas activas
    - GET /api/v2/schools/{id}/ - Ver detalle de escuela
    """
    
    queryset = School.objects.filter(estado='ACTIVO').order_by('codigo')
    serializer_class = SchoolListSerializer
    permission_classes = [AllowAny]
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'codigo']
    ordering_fields = ['nombre', 'codigo']
    ordering = ['codigo']
    
    @extend_schema(
        summary='Listar escuelas activas',
        description='Obtiene lista de escuelas profesionales activas para usar en cartas de presentación.',
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary='Detalle de escuela',
        description='Obtiene información detallada de una escuela profesional.',
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


@extend_schema(tags=['Empresas'])
class CompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Empresas.
    
    Endpoints:
    - GET /api/v2/companies/ - Listar empresas activas
    - GET /api/v2/companies/{id}/ - Ver detalle de empresa
    - POST /api/v2/companies/ - Crear nueva empresa (desde carta de presentación)
    - PUT/PATCH /api/v2/companies/{id}/ - Actualizar empresa (solo admin)
    """
    
    queryset = Company.objects.filter(estado__in=['ACTIVO', 'PENDIENTE']).order_by('nombre')
    permission_classes = [AllowAny]
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'ruc', 'razon_social']
    ordering_fields = ['nombre', 'fecha_registro']
    ordering = ['nombre']
    
    def get_serializer_class(self):
        """Retornar serializer según acción."""
        if self.action == 'create':
            return CompanyCreateSerializer
        return CompanyListSerializer
    
    @extend_schema(
        summary='Listar empresas',
        description='Obtiene lista de empresas activas/pendientes para usar en cartas de presentación.',
        parameters=[
            OpenApiParameter('search', str, description='Buscar por nombre, RUC o razón social'),
            OpenApiParameter('estado', str, description='Filtrar por estado (ACTIVO, PENDIENTE)'),
            OpenApiParameter('sector_economico', str, description='Filtrar por sector'),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary='Detalle de empresa',
        description='Obtiene información detallada de una empresa.',
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        summary='Crear empresa',
        description='''
        Crea una nueva empresa en el sistema.
        
        La empresa se crea en estado PENDIENTE y debe ser validada por un administrador.
        
        **Campos requeridos:**
        - nombre
        - ruc (11 dígitos)
        - direccion
        ''',
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Crear empresa en estado PENDIENTE
        empresa = serializer.save(estado='PENDIENTE')
        
        return Response({
            'success': True,
            'message': 'Empresa creada exitosamente en estado PENDIENTE',
            'data': CompanyListSerializer(empresa).data
        }, status=201)
    
    @extend_schema(
        summary='Buscar empresa por RUC',
        description='Busca una empresa por su RUC.',
    )
    @action(detail=False, methods=['get'], url_path='search-by-ruc')
    def search_by_ruc(self, request):
        """Buscar empresa por RUC."""
        ruc = request.query_params.get('ruc')
        
        if not ruc:
            return Response({'error': 'Debe proporcionar el parámetro RUC'}, status=400)
        
        try:
            empresa = Company.objects.get(ruc=ruc)
            return Response({
                'found': True,
                'data': CompanyListSerializer(empresa).data
            })
        except Company.DoesNotExist:
            return Response({
                'found': False,
                'message': f'No se encontró empresa con RUC {ruc}'
            })
