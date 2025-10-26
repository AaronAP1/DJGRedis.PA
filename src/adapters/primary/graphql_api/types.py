"""
Tipos GraphQL para el sistema de gestión de prácticas profesionales.
"""

import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import FilterSet, CharFilter, DateFilter, NumberFilter
from src.adapters.secondary.database.models import (
    User, Student, Company, Supervisor, Practice, Document, Notification,
    Permission, Role, RolePermission, UserPermission, Avatar,
    School, Branch, PracticeEvaluation, PracticeStatusHistory
)


class UserFilter(FilterSet):
    """Filtros para usuarios."""
    # Usar nombres de campos reales de BD (con alias via properties)
    email = CharFilter(field_name='correo', lookup_expr='icontains')
    first_name = CharFilter(field_name='nombres', lookup_expr='icontains')
    last_name = CharFilter(field_name='apellidos', lookup_expr='icontains')
    role = CharFilter(lookup_expr='exact')

    class Meta:
        model = User
        # Campos reales de BD: correo, nombres, apellidos, activo
        fields = ['correo', 'nombres', 'apellidos', 'activo']


class UserType(DjangoObjectType):
    """Tipo GraphQL para Usuario."""
    
    class Meta:
        model = User
        filterset_class = UserFilter
        # Usar campos reales de BD + properties de compatibilidad funcionarán automáticamente
        fields = (
            'id', 'correo', 'nombres', 'apellidos', 'dni', 'telefono',
            'activo', 'ultimo_acceso', 'fecha_creacion', 'rol_id', 'escuela_id'
        )
    
    full_name = graphene.String()
    photo_url = graphene.String()
    # Alias en español para consumo de frontend
    nombre_completo = graphene.String()
    # Campos legacy (via properties)
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    is_active = graphene.Boolean()
    last_login = graphene.DateTime()
    # Exponer código de estudiante cuando el usuario es PRACTICANTE
    codigo_estudiante = graphene.String()
    
    # Sistema de permisos
    role_obj = graphene.Field('src.adapters.primary.graphql_api.types.RoleType')
    all_permissions = graphene.List(graphene.String)
    permissions_info = graphene.Field('src.adapters.primary.graphql_api.types.UserPermissionsInfo')
    role_permissions = graphene.List('src.adapters.primary.graphql_api.types.PermissionType')
    
    # Campo simplificado: solo permisos efectivos como objetos
    permisos = graphene.List('src.adapters.primary.graphql_api.types.PermissionType')
    
    def resolve_full_name(self, info):
        """Resuelve el nombre completo."""
        return self.get_full_name()

    def resolve_photo_url(self, info):
        """Resuelve la URL de la foto de perfil desde el avatar."""
        return self.avatar.url if hasattr(self, 'avatar') and self.avatar else None

    def resolve_nombre_completo(self, info):
        return self.get_full_name()
    
    def resolve_email(self, info):
        """Exponer alias email."""
        return self.correo
    
    def resolve_first_name(self, info):
        """Exponer alias first_name."""
        return self.nombres

    def resolve_last_name(self, info):
        """Exponer alias last_name."""
        return self.apellidos
    
    def resolve_is_active(self, info):
        """Exponer alias is_active."""
        return self.activo
    
    def resolve_last_login(self, info):
        """Exponer alias last_login."""
        return self.ultimo_acceso

    def resolve_codigo_estudiante(self, info):
        """Resuelve el código de estudiante si el usuario es PRACTICANTE."""
        if hasattr(self, 'student_profile') and self.student_profile:
            return self.student_profile.codigo
        return None
    
    def resolve_role_obj(self, info):
        """Resuelve el objeto Role completo del usuario."""
        # Primero intentar con role_obj (ForeignKey), luego con role (legacy)
        if self.role_obj:
            return self.role_obj
        elif self.role:
            from src.adapters.secondary.database.models import Role
            try:
                return Role.objects.get(code=self.role, is_active=True)
            except Role.DoesNotExist:
                return None
        return None
    
    def resolve_all_permissions(self, info):
        """Resuelve todos los permisos del usuario."""
        # Forzar recálculo sin caché
        return self.get_all_permissions()
    
    def resolve_permissions_info(self, info):
        """Resuelve información detallada de permisos."""
        from src.adapters.primary.graphql_api.types import UserPermissionsInfo
        from src.adapters.secondary.database.models import Permission
        
        role_perms = []
        if self.role_obj:
            role_perms = list(self.role_obj.permissions.filter(is_active=True))
        
        custom_perms = list(self.custom_permissions.filter(
            permission__is_active=True
        ))
        
        # Obtener permisos efectivos (códigos) y convertirlos a objetos Permission
        effective_codes = self.get_all_permissions()
        effective_perms = list(Permission.objects.filter(
            code__in=effective_codes,
            is_active=True
        ))
        
        return UserPermissionsInfo(
            role=self.role_obj,
            role_permissions=role_perms,  # TODOS los permisos del rol
            effective_permissions=effective_perms,  # Solo permisos EFECTIVOS
            custom_permissions=custom_perms,
            all_permissions=effective_codes
        )
    
    def resolve_role_permissions(self, info):
        """Resuelve los permisos del rol del usuario."""
        from src.adapters.secondary.database.models import Role, Permission
        try:
            role = Role.objects.get(code=self.role, is_active=True)
            return role.permissions.filter(is_active=True)
        except Role.DoesNotExist:
            return Permission.objects.none()
    
    def resolve_permisos(self, info):
        """Resuelve SOLO los permisos efectivos del usuario (campo simplificado)."""
        from src.adapters.secondary.database.models import Permission
        
        # Obtener códigos de permisos efectivos
        effective_codes = self.get_all_permissions()
        
        # Convertir a objetos Permission
        return Permission.objects.filter(
            code__in=effective_codes,
            is_active=True
        ).order_by('module', 'code')


class StudentFilter(FilterSet):
    """Filtros para estudiantes."""
    # StudentProfile (Student) tiene: codigo, semestre, promedio, usuario, escuela, rama
    codigo = CharFilter(lookup_expr='icontains')
    estado_academico = CharFilter(lookup_expr='exact')

    class Meta:
        model = Student
        fields = ['codigo', 'semestre', 'promedio', 'estado_academico']


class StudentType(DjangoObjectType):
    """Tipo GraphQL para Estudiante."""
    
    class Meta:
        model = Student
        interfaces = (graphene.relay.Node,)
        filterset_class = StudentFilter
        # Campos reales de StudentProfile: id, usuario, codigo, semestre, promedio, fecha_nacimiento, 
        # direccion, escuela, rama, cv_path, fecha_cv_subido, estado_academico, fecha_creacion
        fields = (
            'id', 'usuario', 'codigo', 'semestre', 'promedio', 'fecha_nacimiento',
            'direccion', 'escuela', 'rama', 'cv_path', 'estado_academico', 'fecha_creacion'
        )
    
    # Campos legacy para compatibilidad
    user = graphene.Field('src.adapters.primary.graphql_api.types.UserType')
    codigo_estudiante = graphene.String()
    semestre_actual = graphene.Int()
    promedio_ponderado = graphene.Float()
    carrera = graphene.Field('src.adapters.primary.graphql_api.types.SchoolType')
    puede_realizar_practica = graphene.Boolean()
    anio_ingreso = graphene.Int()
    edad = graphene.Int()
    
    def resolve_user(self, info):
        """Alias para usuario."""
        return self.usuario
    
    def resolve_codigo_estudiante(self, info):
        """Alias para codigo."""
        return self.codigo
    
    def resolve_semestre_actual(self, info):
        """Alias para semestre."""
        return self.semestre
    
    def resolve_promedio_ponderado(self, info):
        """Alias para promedio."""
        return float(self.promedio) if self.promedio else None
    
    def resolve_carrera(self, info):
        """Alias para escuela."""
        return self.escuela
    
    def resolve_puede_realizar_practica(self, info):
        """Resuelve si puede realizar práctica (semestre >= 6 y promedio >= 12)."""
        return self.semestre >= 6 and self.promedio >= 12

    def resolve_anio_ingreso(self, info):
        """Resuelve el año de ingreso estimado del código."""
        if self.codigo and len(self.codigo) >= 4:
            try:
                return int(self.codigo[:4])
            except ValueError:
                pass
        return None
    
    def resolve_edad(self, info):
        """Resuelve la edad del estudiante."""
        return self.edad


class CompanyFilter(FilterSet):
    """Filtros para empresas."""
    # Company tiene: nombre, razon_social, ruc, sector_economico, estado
    razon_social = CharFilter(lookup_expr='icontains')
    nombre = CharFilter(lookup_expr='icontains')
    ruc = CharFilter(lookup_expr='exact')
    sector_economico = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Company
        fields = ['razon_social', 'nombre', 'ruc', 'sector_economico', 'estado']


class CompanyType(DjangoObjectType):
    """Tipo GraphQL para Empresa."""
    
    class Meta:
        model = Company
        interfaces = (graphene.relay.Node,)
        filterset_class = CompanyFilter
        # Campos reales: id, nombre, ruc, razon_social, direccion, distrito, provincia, 
        # departamento, telefono, correo, sitio_web, sector_economico, tamaño_empresa, 
        # estado, validado_por, fecha_validacion, fecha_registro
        exclude = ('tamaño_empresa',)  # Excluir por caracteres especiales
    
    # Campo con nombre ASCII para evitar caracteres especiales en GraphQL
    tamano_empresa = graphene.String(name='tamanoEmpresa')
    # Aliases legacy
    nombre_comercial = graphene.String()
    email = graphene.String()
    status = graphene.String()
    nombre_para_mostrar = graphene.String()
    puede_recibir_practicantes = graphene.Boolean()
    
    def resolve_tamano_empresa(self, info):
        """Resuelve el tamaño de empresa desde el modelo."""
        return self.tamaño_empresa
    
    def resolve_nombre_comercial(self, info):
        """Alias para nombre."""
        return self.nombre
    
    def resolve_email(self, info):
        """Alias para correo."""
        return self.correo
    
    def resolve_status(self, info):
        """Alias para estado."""
        return self.estado

    def resolve_nombre_para_mostrar(self, info):
        """Resuelve el nombre para mostrar."""
        return self.razon_social or self.nombre

    def resolve_puede_recibir_practicantes(self, info):
        """Resuelve si puede recibir practicantes."""
        return self.estado == 'ACTIVO'


class SupervisorFilter(FilterSet):
    """Filtros para supervisores."""
    # SupervisorProfile tiene: usuario, empresa, cargo, telefono_trabajo, correo_trabajo, 
    # años_experiencia, especialidad
    cargo = CharFilter(lookup_expr='icontains')
    especialidad = CharFilter(lookup_expr='icontains')
    # Exponer filtro ASCII mapeado al campo Django con ñ
    anios_experiencia = NumberFilter(field_name='años_experiencia')

    class Meta:
        model = Supervisor
        # NO incluir años_experiencia directamente (tiene ñ)
        fields = ['cargo', 'especialidad']


class SupervisorType(DjangoObjectType):
    """Tipo GraphQL para Supervisor."""
    
    class Meta:
        model = Supervisor
        interfaces = (graphene.relay.Node,)
        filterset_class = SupervisorFilter
        # Excluir campo con ñ para evitar conversión automática a camelCase inválido
        exclude = ('años_experiencia',)

    # Campo con nombre ASCII para evitar caracteres especiales en GraphQL
    anios_experiencia = graphene.Int(name='aniosExperiencia')
    
    def resolve_anios_experiencia(self, info):
        """Resuelve los años de experiencia desde el modelo."""
        return self.años_experiencia


class PracticeFilter(FilterSet):
    """Filtros para prácticas."""
    # Practice tiene: titulo, descripcion, fecha_inicio, fecha_fin, estado, modalidad
    titulo = CharFilter(lookup_expr='icontains')
    descripcion = CharFilter(lookup_expr='icontains')
    fecha_inicio = DateFilter(lookup_expr='gte')
    fecha_fin = DateFilter(lookup_expr='lte')

    class Meta:
        model = Practice
        fields = ['titulo', 'estado', 'modalidad', 'remunerada']


class PracticeType(DjangoObjectType):
    """Tipo GraphQL para Práctica."""
    
    class Meta:
        model = Practice
        interfaces = (graphene.relay.Node,)
        filterset_class = PracticeFilter
        # Campos reales del modelo: practicante, empresa, supervisor, titulo, descripcion, 
        # objetivos, fecha_inicio, fecha_fin, horas_totales, horas_completadas, 
        # modalidad, estado, remunerada, monto_remuneracion, coordinador, secretaria,
        # fecha_creacion, fecha_actualizacion, observaciones
        fields = (
            'id', 'practicante', 'empresa', 'supervisor', 'coordinador', 'secretaria',
            'titulo', 'descripcion', 'objetivos', 'fecha_inicio', 'fecha_fin', 
            'horas_totales', 'horas_completadas', 'modalidad', 'estado', 
            'remunerada', 'monto_remuneracion', 'fecha_creacion', 'fecha_actualizacion', 
            'observaciones'
        )

    # Resolvers para campos legacy (compatibilidad)
    student = graphene.Field('src.adapters.primary.graphql_api.types.StudentType')
    company = graphene.Field('src.adapters.primary.graphql_api.types.CompanyType')
    status = graphene.String()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    duracion_dias = graphene.Int()
    esta_activa = graphene.Boolean()
    progreso_porcentual = graphene.Float()
    
    def resolve_student(self, info):
        """Compatibilidad: student mapea a practicante."""
        return self.practicante
    
    def resolve_company(self, info):
        """Compatibilidad: company mapea a empresa."""
        return self.empresa
    
    def resolve_status(self, info):
        """Compatibilidad: status mapea a estado."""
        return self.estado
    
    def resolve_created_at(self, info):
        """Compatibilidad: created_at mapea a fecha_creacion."""
        return self.fecha_creacion
    
    def resolve_updated_at(self, info):
        """Compatibilidad: updated_at mapea a fecha_actualizacion."""
        return self.fecha_actualizacion
    
    def resolve_duracion_dias(self, info):
        """Resuelve la duración en días."""
        if self.fecha_inicio and self.fecha_fin:
            return (self.fecha_fin - self.fecha_inicio).days
        return 0

    def resolve_esta_activa(self, info):
        """Resuelve si está activa."""
        return self.estado == 'EN_CURSO'

    def resolve_progreso_porcentual(self, info):
        """Resuelve el progreso porcentual."""
        if self.horas_totales > 0:
            return min((self.horas_completadas / self.horas_totales) * 100, 100)
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
        # Excluir campo con ñ para evitar conversión automática a camelCase inválido
        exclude = ('tamaño_bytes',)

    # Campos con nombres ASCII para evitar caracteres especiales en GraphQL
    tamano_bytes = graphene.Int(name='tamanoBytes')
    tamano_legible = graphene.String(name='tamanoLegible')
    es_imagen = graphene.Boolean()
    es_pdf = graphene.Boolean()
    
    def resolve_tamano_bytes(self, info):
        """Resuelve el tamaño en bytes desde el modelo."""
        return self.tamaño_bytes
    
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
        # Campos reales: id, codigo, nombre, descripcion, module, is_active, created_at
        fields = ('id', 'codigo', 'nombre', 'descripcion', 'module', 'is_active', 'created_at')
    
    # Resolvers para campos legacy (compatibilidad)
    code = graphene.String()
    name = graphene.String()
    description = graphene.String()
    
    def resolve_code(self, info):
        """Compatibilidad: code mapea a codigo."""
        return self.codigo
    
    def resolve_name(self, info):
        """Compatibilidad: name mapea a nombre."""
        return self.nombre
    
    def resolve_description(self, info):
        """Compatibilidad: description mapea a descripcion."""
        return self.descripcion


class RoleType(DjangoObjectType):
    """Tipo GraphQL para Roles."""
    
    class Meta:
        model = Role
        # Campos reales: id, nombre, descripcion, permisos, fecha_creacion
        fields = ('id', 'nombre', 'descripcion', 'permisos', 'fecha_creacion')
    
    # Resolvers para campos legacy (compatibilidad)
    code = graphene.String()
    name = graphene.String()
    description = graphene.String()
    permissions = graphene.List(PermissionType)
    permissions_count = graphene.Int()
    users_count = graphene.Int()
    
    def resolve_code(self, info):
        """Compatibilidad: code mapea a nombre."""
        return self.nombre
    
    def resolve_name(self, info):
        """Compatibilidad: name mapea a nombre."""
        return self.nombre
    
    def resolve_description(self, info):
        """Compatibilidad: description mapea a descripcion."""
        return self.descripcion
    
    def resolve_permissions(self, info):
        """Resuelve los permisos del rol (desde tabla upeu_permiso si existe)."""
        return self.permissions.filter(is_active=True)
    
    def resolve_permissions_count(self, info):
        """Cuenta los permisos activos del rol."""
        return self.permissions.filter(is_active=True).count()
    
    def resolve_users_count(self, info):
        """Cuenta los usuarios activos con este rol."""
        return User.objects.filter(rol=self, activo=True).count()


class UserPermissionType(DjangoObjectType):
    """Tipo GraphQL para Permisos de Usuario."""
    
    class Meta:
        model = UserPermission
        fields = ('id', 'usuario', 'permiso', 'permiso_tipo', 'granted_at')
    
    # Resolvers para campos legacy (compatibilidad)
    user = graphene.Field('src.adapters.primary.graphql_api.types.UserType')
    permission = graphene.Field('src.adapters.primary.graphql_api.types.PermissionType')
    permission_type = graphene.String()
    
    def resolve_user(self, info):
        """Compatibilidad: user mapea a usuario."""
        return self.usuario
    
    def resolve_permission(self, info):
        """Compatibilidad: permission mapea a permiso."""
        return self.permiso
    
    def resolve_permission_type(self, info):
        """Compatibilidad: permission_type mapea a permiso_tipo."""
        return self.permiso_tipo


class UserPermissionsInfo(graphene.ObjectType):
    """Información completa de permisos de un usuario."""
    role = graphene.Field(RoleType)
    role_permissions = graphene.List(PermissionType)  # TODOS los permisos del rol (sin filtrar)
    effective_permissions = graphene.List(PermissionType)  # Solo permisos EFECTIVOS (rol - revocados + otorgados)
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


# ============================================================================
# TIPOS GRAPHQL PARA NUEVOS MODELOS
# ============================================================================

class SchoolFilter(FilterSet):
    """Filtros para escuelas profesionales."""
    codigo = CharFilter(lookup_expr='icontains')
    nombre = CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = School
        fields = ['codigo', 'nombre', 'estado', 'descripcion']


class SchoolType(DjangoObjectType):
    """Tipo GraphQL para Escuela Profesional."""
    
    class Meta:
        model = School
        filterset_class = SchoolFilter
        fields = (
            'id', 'codigo', 'nombre', 'descripcion', 'estado', 'fecha_creacion'
        )
    
    # Resolvers para campos legacy (compatibilidad)
    activa = graphene.Boolean()
    created_at = graphene.DateTime()
    coordinador_nombre = graphene.String()
    total_estudiantes = graphene.Int()
    total_ramas = graphene.Int()
    ramas = graphene.List('src.adapters.primary.graphql_api.types.BranchType')
    
    def resolve_activa(self, info):
        """Compatibilidad: activa mapea a estado == 'ACTIVO'."""
        return self.estado == 'ACTIVO'
    
    def resolve_created_at(self, info):
        """Compatibilidad: created_at mapea a fecha_creacion."""
        return self.fecha_creacion
    
    def resolve_coordinador_nombre(self, info):
        """Resuelve el nombre del coordinador (si existe)."""
        # El modelo actual no tiene coordinador FK
        return None
    
    def resolve_total_estudiantes(self, info):
        """Resuelve total de estudiantes."""
        # Usar el related_name desde StudentProfile
        return Student.objects.filter(escuela=self).count()
    
    def resolve_total_ramas(self, info):
        """Resuelve total de ramas activas."""
        return self.branches.filter(activa=True).count()
    
    def resolve_ramas(self, info):
        """Resuelve las ramas de la escuela."""
        return self.branches.filter(activa=True)


class BranchFilter(FilterSet):
    """Filtros para ramas/especialidades."""
    nombre = CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Branch
        fields = ['nombre', 'escuela', 'activa', 'descripcion']


class BranchType(DjangoObjectType):
    """Tipo GraphQL para Rama/Especialidad."""
    
    class Meta:
        model = Branch
        filterset_class = BranchFilter
        fields = (
            'id', 'nombre', 'descripcion', 'escuela', 'activa', 'fecha_creacion'
        )
    
    # Resolvers para campos legacy (compatibilidad)
    school = graphene.Field('src.adapters.primary.graphql_api.types.SchoolType')
    created_at = graphene.DateTime()
    escuela_nombre = graphene.String()
    escuela_codigo = graphene.String()
    total_estudiantes = graphene.Int()
    
    def resolve_school(self, info):
        """Compatibilidad: school mapea a escuela."""
        return self.escuela
    
    def resolve_created_at(self, info):
        """Compatibilidad: created_at mapea a fecha_creacion."""
        return self.fecha_creacion
    
    def resolve_escuela_nombre(self, info):
        """Resuelve el nombre de la escuela."""
        return self.escuela.nombre
    
    def resolve_escuela_codigo(self, info):
        """Resuelve el código de la escuela."""
        return self.escuela.codigo
    
    def resolve_total_estudiantes(self, info):
        """Resuelve total de estudiantes en la rama."""
        # Usar Student (alias de StudentProfile)
        return Student.objects.filter(rama=self).count()


class PracticeEvaluationFilter(FilterSet):
    """Filtros para evaluaciones de prácticas."""
    tipo_evaluador = CharFilter(lookup_expr='exact')
    periodo_evaluacion = CharFilter(lookup_expr='exact')
    fecha_evaluacion = DateFilter()
    
    class Meta:
        model = PracticeEvaluation
        fields = ['practica', 'evaluador', 'tipo_evaluador', 'periodo_evaluacion']


class PracticeEvaluationType(DjangoObjectType):
    """Tipo GraphQL para Evaluación de Práctica."""
    
    class Meta:
        model = PracticeEvaluation
        filterset_class = PracticeEvaluationFilter
        fields = (
            'id', 'practica', 'evaluador', 'tipo_evaluador', 'periodo_evaluacion',
            'fecha_evaluacion', 'puntaje_total', 'criterios_evaluacion',
            'comentarios', 'recomendaciones'
        )
    
    # Resolvers para campos legacy (compatibilidad)
    practice = graphene.Field('src.adapters.primary.graphql_api.types.PracticeType')
    evaluator = graphene.Field('src.adapters.primary.graphql_api.types.UserType')
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    status = graphene.String()
    practica_titulo = graphene.String()
    estudiante_nombre = graphene.String()
    evaluador_nombre = graphene.String()
    status_display = graphene.String()
    
    def resolve_practice(self, info):
        """Compatibilidad: practice mapea a practica."""
        return self.practica
    
    def resolve_evaluator(self, info):
        """Compatibilidad: evaluator mapea a evaluador."""
        return self.evaluador
    
    def resolve_created_at(self, info):
        """Compatibilidad: created_at mapea a fecha_evaluacion."""
        return self.fecha_evaluacion
    
    def resolve_updated_at(self, info):
        """Compatibilidad: updated_at mapea a fecha_evaluacion."""
        return self.fecha_evaluacion
    
    def resolve_status(self, info):
        """Compatibilidad: status siempre APPROVED."""
        return 'APPROVED'
    
    def resolve_practica_titulo(self, info):
        """Resuelve el título de la práctica."""
        return self.practica.titulo
    
    def resolve_estudiante_nombre(self, info):
        """Resuelve el nombre del estudiante."""
        practicante = self.practica.practicante
        if practicante and practicante.usuario:
            return f"{practicante.usuario.nombres} {practicante.usuario.apellidos}"
        return None
    
    def resolve_evaluador_nombre(self, info):
        """Resuelve el nombre del evaluador."""
        if self.evaluador:
            return f"{self.evaluador.nombres} {self.evaluador.apellidos}"
        return None
    
    def resolve_status_display(self, info):
        """Resuelve el status en español."""
        return 'Aprobado'  # Siempre aprobado (compatibilidad)


class PracticeStatusHistoryFilter(FilterSet):
    """Filtros para historial de estados de práctica."""
    estado_anterior = CharFilter(lookup_expr='exact')
    estado_nuevo = CharFilter(lookup_expr='exact')
    fecha_cambio = DateFilter()
    
    class Meta:
        model = PracticeStatusHistory
        fields = ['practice', 'usuario_responsable', 'estado_anterior', 'estado_nuevo']


class PracticeStatusHistoryType(DjangoObjectType):
    """Tipo GraphQL para Historial de Estados de Práctica."""
    
    class Meta:
        model = PracticeStatusHistory
        filterset_class = PracticeStatusHistoryFilter
        fields = (
            'id', 'practice', 'estado_anterior', 'estado_nuevo',
            'usuario_responsable', 'motivo', 'metadata', 'fecha_cambio'
        )
    
    practica_titulo = graphene.String()
    responsable_nombre = graphene.String()
    
    def resolve_practica_titulo(self, info):
        """Resuelve el título de la práctica."""
        return self.practice.titulo
    
    def resolve_responsable_nombre(self, info):
        """Resuelve el nombre del responsable."""
        return self.usuario_responsable.get_full_name() if self.usuario_responsable else None


# ============================================================================
# INPUTS GRAPHQL PARA NUEVOS MODELOS
# ============================================================================

class SchoolInput(graphene.InputObjectType):
    """Input para crear/actualizar escuela profesional."""
    codigo = graphene.String(required=True)
    nombre = graphene.String(required=True)
    facultad = graphene.String(required=True)
    coordinador_id = graphene.ID()
    activa = graphene.Boolean()


class BranchInput(graphene.InputObjectType):
    """Input para crear/actualizar rama/especialidad."""
    nombre = graphene.String(required=True)
    school_id = graphene.ID(required=True)
    activa = graphene.Boolean()


class PracticeEvaluationInput(graphene.InputObjectType):
    """Input para crear/actualizar evaluación de práctica."""
    practice_id = graphene.ID(required=True)
    evaluator_id = graphene.ID(required=True)
    tipo_evaluador = graphene.String(required=True)
    periodo_evaluacion = graphene.String(required=True)
    fecha_evaluacion = graphene.Date()
    puntaje_total = graphene.Float(required=True)
    criterios_evaluacion = graphene.JSONString()
    comentarios = graphene.String()
    recomendaciones = graphene.String()
    fortalezas = graphene.String()
    areas_mejora = graphene.String()

