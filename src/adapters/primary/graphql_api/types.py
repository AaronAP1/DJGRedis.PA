"""
Tipos GraphQL para el sistema de gestión de prácticas profesionales.
"""

import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import FilterSet, CharFilter, DateFilter, NumberFilter
from src.adapters.secondary.database.models import (
    User, Student, Company, Supervisor, Practice, Document, Notification,
    Permission, Role, RolePermission, UserPermission, Avatar
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
            'is_active', 'last_login', 'created_at', 'updated_at', 'avatar'
        )

    # ID real de la base de datos (UUID sin codificar)
    uuid = graphene.String()
    
    full_name = graphene.String()
    photo_url = graphene.String()
    # Alias en español para consumo de frontend
    nombre_completo = graphene.String()
    nombres = graphene.String()
    apellidos = graphene.String()
    # Exponer código de estudiante cuando el usuario es PRACTICANTE
    codigo_estudiante = graphene.String()
    
    # Sistema de permisos
    role_obj = graphene.Field('src.adapters.primary.graphql_api.types.RoleType')
    all_permissions = graphene.List(graphene.String)
    permissions_info = graphene.Field('src.adapters.primary.graphql_api.types.UserPermissionsInfo')
    role_permissions = graphene.List('src.adapters.primary.graphql_api.types.PermissionType')
    
    def resolve_uuid(self, info):
        """Resuelve el UUID real de la base de datos."""
        return str(self.pk)
    
    def resolve_full_name(self, info):
        """Resuelve el nombre completo."""
        return self.get_full_name()

    def resolve_photo_url(self, info):
        """Resuelve la URL de la foto de perfil desde el avatar."""
        return self.avatar.url if self.avatar else None

    def resolve_nombre_completo(self, info):
        return self.get_full_name()

    def resolve_nombres(self, info):
        return self.first_name

    def resolve_apellidos(self, info):
        return self.last_name

    def resolve_codigo_estudiante(self, info):
        """Resuelve el código de estudiante si el usuario es PRACTICANTE."""
        if self.role == 'PRACTICANTE' and hasattr(self, 'student_profile'):
            return self.student_profile.codigo_estudiante
        return None
    
    def resolve_role_obj(self, info):
        """Resuelve el objeto Role completo del usuario."""
        from src.adapters.secondary.database.models import Role
        try:
            return Role.objects.get(code=self.role, is_active=True)
        except Role.DoesNotExist:
            return None
    
    def resolve_all_permissions(self, info):
        """Resuelve todos los permisos del usuario."""
        return self.get_all_permissions()
    
    def resolve_permissions_info(self, info):
        """Resuelve información detallada de permisos."""
        from src.adapters.primary.graphql_api.types import UserPermissionsInfo
        
        role_perms = []
        if self.role_obj:
            role_perms = list(self.role_obj.permissions.filter(is_active=True))
        
        custom_perms = list(self.custom_permissions.filter(
            permission__is_active=True
        ))
        
        return UserPermissionsInfo(
            role=self.role_obj,
            role_permissions=role_perms,
            custom_permissions=custom_perms,
            all_permissions=self.get_all_permissions()
        )
    
    def resolve_role_permissions(self, info):
        """Resuelve los permisos del rol del usuario."""
        from src.adapters.secondary.database.models import Role, Permission
        try:
            role = Role.objects.get(code=self.role, is_active=True)
            return role.permissions.filter(is_active=True)
        except Role.DoesNotExist:
            return Permission.objects.none()


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
    """Input para actualizar el perfil del usuario autenticado (solo nombres y apellidos)."""
    first_name = graphene.String()
    last_name = graphene.String()
    # username y email NO se pueden editar por el usuario


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


# ===== TIPOS PARA SISTEMA DE ROLES Y PERMISOS =====

class PermissionType(DjangoObjectType):
    """Tipo GraphQL para Permisos."""
    
    class Meta:
        model = Permission
        fields = ('id', 'code', 'name', 'description', 'module', 'is_active', 'created_at')


class RoleType(DjangoObjectType):
    """Tipo GraphQL para Roles."""
    
    class Meta:
        model = Role
        fields = ('id', 'code', 'name', 'description', 'is_active', 'is_system', 
                 'created_at', 'updated_at')
    
    permissions = graphene.List(PermissionType)
    permissions_count = graphene.Int()
    users_count = graphene.Int()
    
    def resolve_permissions(self, info):
        return self.permissions.filter(is_active=True)
    
    def resolve_permissions_count(self, info):
        return self.permissions.filter(is_active=True).count()
    
    def resolve_users_count(self, info):
        return self.users.filter(is_active=True).count()


class UserPermissionType(DjangoObjectType):
    """Tipo GraphQL para Permisos de Usuario."""
    
    class Meta:
        model = UserPermission
        fields = ('id', 'user', 'permission', 'permission_type', 'reason', 
                 'granted_by', 'granted_at', 'expires_at')
    
    is_expired = graphene.Boolean()
    def resolve_is_expired(self, info):
        return self.is_expired


class UserPermissionsInfo(graphene.ObjectType):
    """Información completa de permisos de un usuario."""
    role = graphene.Field(RoleType)
    role_permissions = graphene.List(PermissionType)
    custom_permissions = graphene.List(UserPermissionType)
    all_permissions = graphene.List(graphene.String)


class AvatarType(DjangoObjectType):
    """Tipo GraphQL para avatares por rol."""
    
    class Meta:
        model = Avatar
        fields = ('id', 'url', 'role', 'is_active', 'created_at')


class EmpresaRucType(graphene.ObjectType):
    """Tipo GraphQL para información de empresa desde API RUC."""
    ruc = graphene.String()
    razon_social = graphene.String()
    nombre_comercial = graphene.String()
    direccion = graphene.String()
    departamento = graphene.String()
    provincia = graphene.String()
    distrito = graphene.String()
    estado = graphene.String()
    condicion = graphene.String()


class PermissionInput(graphene.InputObjectType):
    """Input para crear/actualizar permisos."""
    code = graphene.String(required=True)
    name = graphene.String(required=True)
    description = graphene.String()
    module = graphene.String(required=True)


class RoleInput(graphene.InputObjectType):
    """Input para crear/actualizar roles."""
    code = graphene.String(required=True)
    name = graphene.String(required=True)
    description = graphene.String()
    permission_ids = graphene.List(graphene.ID)
