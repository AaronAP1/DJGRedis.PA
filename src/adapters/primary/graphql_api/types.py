"""
Tipos GraphQL para el sistema de gestión de prácticas profesionales.
"""

import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import FilterSet, CharFilter, DateFilter, NumberFilter
from src.adapters.secondary.database.models import (
    User, Student, Company, Supervisor, Practice, Document, Notification
)


class UserFilter(FilterSet):
    """Filtros para usuarios."""
    email = CharFilter(lookup_expr='icontains')
    first_name = CharFilter(lookup_expr='icontains')
    last_name = CharFilter(lookup_expr='icontains')
    role = CharFilter(lookup_expr='exact')

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'role', 'is_active']


class UserType(DjangoObjectType):
    """Tipo GraphQL para Usuario."""
    
    class Meta:
        model = User
        interfaces = (graphene.relay.Node,)
        filterset_class = UserFilter
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'role', 
            'is_active', 'last_login', 'created_at', 'updated_at', 'photo'
        )

    full_name = graphene.String()
    photo_url = graphene.String()
    # Alias en español para consumo de frontend
    nombre_completo = graphene.String()
    nombres = graphene.String()
    apellidos = graphene.String()
    # Exponer código de estudiante cuando el usuario es PRACTICANTE
    codigo_estudiante = graphene.String()
    
    def resolve_full_name(self, info):
        """Resuelve el nombre completo."""
        return self.get_full_name()

    def resolve_photo_url(self, info):
        request = info.context
        try:
            if getattr(self, 'photo', None):
                url = self.photo.url
                if url and hasattr(request, 'build_absolute_uri'):
                    return request.build_absolute_uri(url)
                return url
        except Exception:
            return None
        return None

    def resolve_nombre_completo(self, info):
        return self.get_full_name()

    def resolve_nombres(self, info):
        return self.first_name

    def resolve_apellidos(self, info):
        return self.last_name

    def resolve_codigo_estudiante(self, info):
        """Retorna el código de estudiante si el usuario es PRACTICANTE."""
        try:
            if getattr(self, 'role', None) == 'PRACTICANTE':
                sp = getattr(self, 'student_profile', None)
                if sp and getattr(sp, 'codigo_estudiante', None):
                    return sp.codigo_estudiante
        except Exception:
            return None
        return None


class StudentFilter(FilterSet):
    """Filtros para estudiantes."""
    codigo_estudiante = CharFilter(lookup_expr='icontains')
    carrera = CharFilter(lookup_expr='icontains')
    documento_numero = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Student
        fields = ['codigo_estudiante', 'carrera', 'documento_numero', 'semestre_actual']


class StudentType(DjangoObjectType):
    """Tipo GraphQL para Estudiante."""
    
    class Meta:
        model = Student
        interfaces = (graphene.relay.Node,)
        filterset_class = StudentFilter
        fields = (
            'id', 'user', 'codigo_estudiante', 'documento_tipo', 'documento_numero',
            'telefono', 'direccion', 'carrera', 'semestre_actual', 'promedio_ponderado',
            'created_at', 'updated_at'
        )

    puede_realizar_practica = graphene.Boolean()
    anio_ingreso = graphene.Int()
    
    def resolve_puede_realizar_practica(self, info):
        """Resuelve si puede realizar práctica."""
        return self.puede_realizar_practica

    def resolve_anio_ingreso(self, info):
        """Resuelve el año de ingreso."""
        return self.año_ingreso


class CompanyFilter(FilterSet):
    """Filtros para empresas."""
    razon_social = CharFilter(lookup_expr='icontains')
    nombre_comercial = CharFilter(lookup_expr='icontains')
    ruc = CharFilter(lookup_expr='exact')
    sector_economico = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Company
        fields = ['razon_social', 'nombre_comercial', 'ruc', 'sector_economico', 'status']


class CompanyType(DjangoObjectType):
    """Tipo GraphQL para Empresa."""
    
    class Meta:
        model = Company
        interfaces = (graphene.relay.Node,)
        filterset_class = CompanyFilter
        fields = (
            'id', 'ruc', 'razon_social', 'nombre_comercial', 'direccion',
            'telefono', 'email', 'sector_economico',
            'status', 'fecha_validacion', 'created_at', 'updated_at'
        )

    # Exponer nombre ASCII mapeando al campo Django con ñ
    tamano_empresa = graphene.String(source='tamaño_empresa')

    nombre_para_mostrar = graphene.String()
    puede_recibir_practicantes = graphene.Boolean()
    
    def resolve_nombre_para_mostrar(self, info):
        """Resuelve el nombre para mostrar."""
        return self.nombre_para_mostrar

    def resolve_puede_recibir_practicantes(self, info):
        """Resuelve si puede recibir practicantes."""
        return self.puede_recibir_practicantes


class SupervisorFilter(FilterSet):
    """Filtros para supervisores."""
    cargo = CharFilter(lookup_expr='icontains')
    documento_numero = CharFilter(lookup_expr='icontains')

    # Exponer filtro ASCII mapeado al campo Django con ñ
    anios_experiencia = NumberFilter(field_name='años_experiencia')

    class Meta:
        model = Supervisor
        fields = ['cargo', 'documento_numero']


class SupervisorType(DjangoObjectType):
    """Tipo GraphQL para Supervisor."""
    
    class Meta:
        model = Supervisor
        interfaces = (graphene.relay.Node,)
        filterset_class = SupervisorFilter
        fields = (
            'id', 'user', 'company', 'documento_tipo', 'documento_numero',
            'cargo', 'telefono', 'created_at', 'updated_at'
        )

    # Exponer nombre ASCII mapeando al campo Django con ñ
    anios_experiencia = graphene.Int(source='años_experiencia')


class PracticeFilter(FilterSet):
    """Filtros para prácticas."""
    titulo = CharFilter(lookup_expr='icontains')
    area_practica = CharFilter(lookup_expr='icontains')
    fecha_inicio = DateFilter(lookup_expr='gte')
    fecha_fin = DateFilter(lookup_expr='lte')

    class Meta:
        model = Practice
        fields = ['titulo', 'area_practica', 'status', 'modalidad']


class PracticeType(DjangoObjectType):
    """Tipo GraphQL para Práctica."""
    
    class Meta:
        model = Practice
        interfaces = (graphene.relay.Node,)
        filterset_class = PracticeFilter
        fields = (
            'id', 'student', 'company', 'supervisor', 'titulo', 'descripcion',
            'objetivos', 'fecha_inicio', 'fecha_fin', 'horas_totales',
            'modalidad', 'area_practica', 'status', 'calificacion_final',
            'observaciones', 'created_at', 'updated_at'
        )

    duracion_dias = graphene.Int()
    esta_activa = graphene.Boolean()
    progreso_porcentual = graphene.Float()
    
    def resolve_duracion_dias(self, info):
        """Resuelve la duración en días."""
        return self.duracion_dias

    def resolve_esta_activa(self, info):
        """Resuelve si está activa."""
        return self.esta_activa

    def resolve_progreso_porcentual(self, info):
        """Resuelve el progreso porcentual."""
        if self.fecha_inicio and self.fecha_fin:
            from datetime import datetime
            ahora = datetime.now()
            if ahora < self.fecha_inicio:
                return 0.0
            if ahora >= self.fecha_fin:
                return 100.0
            dias_transcurridos = (ahora - self.fecha_inicio).days
            dias_totales = self.duracion_dias
            if dias_totales == 0:
                return 0.0
            return (dias_transcurridos / dias_totales) * 100
        return 0.0


class DocumentFilter(FilterSet):
    """Filtros para documentos."""
    nombre_archivo = CharFilter(lookup_expr='icontains')
    tipo = CharFilter(lookup_expr='exact')

    class Meta:
        model = Document
        fields = ['nombre_archivo', 'tipo', 'aprobado']


class DocumentType(DjangoObjectType):
    """Tipo GraphQL para Documento."""
    
    class Meta:
        model = Document
        interfaces = (graphene.relay.Node,)
        filterset_class = DocumentFilter
        fields = (
            'id', 'practice', 'tipo', 'nombre_archivo',
            'mime_type', 'subido_por', 'aprobado', 'fecha_aprobacion',
            'aprobado_por', 'created_at', 'updated_at'
        )

    # Exponer nombres ASCII mapeando a campos/propiedades con acentos
    tamano_bytes = graphene.Int(source='tamaño_bytes')
    tamano_legible = graphene.String()
    es_imagen = graphene.Boolean()
    es_pdf = graphene.Boolean()
    
    def resolve_tamano_legible(self, info):
        """Resuelve el tamaño legible."""
        return self.tamaño_legible

    def resolve_es_imagen(self, info):
        """Resuelve si es imagen."""
        return self.es_imagen

    def resolve_es_pdf(self, info):
        """Resuelve si es PDF."""
        return self.es_pdf


class NotificationFilter(FilterSet):
    """Filtros para notificaciones."""
    titulo = CharFilter(lookup_expr='icontains')
    tipo = CharFilter(lookup_expr='exact')

    class Meta:
        model = Notification
        fields = ['titulo', 'tipo', 'leida']


class NotificationType(DjangoObjectType):
    """Tipo GraphQL para Notificación."""
    
    class Meta:
        model = Notification
        interfaces = (graphene.relay.Node,)
        filterset_class = NotificationFilter
        fields = (
            'id', 'user', 'titulo', 'mensaje', 'tipo', 'leida',
            'fecha_lectura', 'accion_url', 'created_at', 'updated_at'
        )

    es_importante = graphene.Boolean()
    
    def resolve_es_importante(self, info):
        """Resuelve si es importante."""
        return self.es_importante


# Tipos de entrada para mutaciones
class UserInput(graphene.InputObjectType):
    """Input para crear/actualizar usuario."""
    email = graphene.String(required=True)
    username = graphene.String()
    first_name = graphene.String(required=True)
    last_name = graphene.String(required=True)
    role = graphene.String(required=True)
    password = graphene.String()
    is_active = graphene.Boolean()
    # Solo para rol PRACTICANTE (creación manual)
    codigo_estudiante = graphene.String()


class UserUpdateInput(graphene.InputObjectType):
    """Input para actualizar usuario (todos los campos opcionales)."""
    email = graphene.String()
    username = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    role = graphene.String()
    password = graphene.String()
    is_active = graphene.Boolean()


class ProfileInput(graphene.InputObjectType):
    """Input para actualizar el perfil del usuario autenticado."""
    first_name = graphene.String()
    last_name = graphene.String()
    username = graphene.String()


class StudentInput(graphene.InputObjectType):
    """Input para crear/actualizar estudiante."""
    user_id = graphene.ID(required=True)
    codigo_estudiante = graphene.String(required=True)
    documento_tipo = graphene.String(required=True)
    documento_numero = graphene.String(required=True)
    telefono = graphene.String()
    direccion = graphene.String()
    carrera = graphene.String()
    semestre_actual = graphene.Int()
    promedio_ponderado = graphene.Float()


class CompanyInput(graphene.InputObjectType):
    """Input para crear/actualizar empresa."""
    ruc = graphene.String(required=True)
    razon_social = graphene.String(required=True)
    nombre_comercial = graphene.String()
    direccion = graphene.String()
    telefono = graphene.String()
    email = graphene.String()
    sector_economico = graphene.String()
    tamano_empresa = graphene.String()


class PracticeInput(graphene.InputObjectType):
    """Input para crear/actualizar práctica."""
    student_id = graphene.ID(required=True)
    company_id = graphene.ID(required=True)
    supervisor_id = graphene.ID()
    titulo = graphene.String(required=True)
    descripcion = graphene.String()
    objetivos = graphene.List(graphene.String)
    fecha_inicio = graphene.DateTime()
    fecha_fin = graphene.DateTime()
    horas_totales = graphene.Int()
    modalidad = graphene.String()
    area_practica = graphene.String()
