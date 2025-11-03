"""
Modelos de Django para el sistema de gestión de prácticas profesionales.
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from uuid import uuid4
import os
import secrets
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

# Importar get_user_model después de definir User para evitar circular import
User = get_user_model


class CustomUserManager(BaseUserManager):
    """Manager personalizado para el modelo User - ADAPTADO A upeu_usuario."""

    def create_user(self, correo, password=None, **extra_fields):
        """Crea y guarda un usuario regular."""
        if not correo:
            raise ValueError('El correo es obligatorio')
        
        correo = self.normalize_email(correo)
        
        # Validar DNI obligatorio
        if 'dni' not in extra_fields:
            raise ValueError('El DNI es obligatorio')
        
        user = self.model(correo=correo, **extra_fields)
        user.set_password(password)  # Esto guardará en hash_contraseña via property
        user.save(using=self._db)
        return user

    def create_superuser(self, correo, password=None, **extra_fields):
        """
        Crea y guarda un superusuario con rol ADMINISTRADOR.
        Si no se proporciona contraseña, usa el DNI como contraseña por defecto.
        """
        extra_fields.setdefault('activo', True)
        
        # Si no hay contraseña, usar el DNI como contraseña por defecto
        if password is None or password == '':
            if 'dni' in extra_fields:
                password = extra_fields['dni']
                print(f"⚠️  Usando DNI como contraseña por defecto. Recuerda cambiarla después.")
            else:
                raise ValueError('Debe proporcionar una contraseña o DNI')
        
        # Asignar rol ADMINISTRADOR si existe
        if 'rol_id' not in extra_fields:
            try:
                # Lazy import para evitar circular dependency
                from src.adapters.secondary.database.models import Role
                admin_role = Role.objects.get(nombre='ADMINISTRADOR')
                extra_fields['rol_id'] = admin_role
            except:
                pass  # Si no existe el rol, continuar sin él

        return self.create_user(correo, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de Usuario personalizado - ADAPTADO A BD EXISTENTE upeu_usuario.
    Estructura real PostgreSQL:
    - correo (no email)
    - hash_contraseña (no password)
    - nombres, apellidos (no first_name, last_name)
    - dni (nuevo campo obligatorio)
    - rol_id (FK a upeu_rol)
    - escuela_id (FK a upeu_escuela)
    """
    
    ROLE_CHOICES = [
        ('PRACTICANTE', 'Practicante'),
        ('SUPERVISOR', 'Supervisor'),
        ('COORDINADOR', 'Coordinador'),
        ('SECRETARIA', 'Secretaria'),
        ('ADMINISTRADOR', 'Administrador'),
    ]

    # Campos mapeados a estructura real de upeu_usuario
    id = models.AutoField(primary_key=True, db_column='id')  # INTEGER en BD real
    correo = models.EmailField('Email', max_length=100, unique=True, db_column='correo')
    hash_contraseña = models.CharField('Contraseña', max_length=255, db_column='hash_contraseña')
    nombres = models.CharField('Nombres', max_length=100, db_column='nombres')
    apellidos = models.CharField('Apellidos', max_length=100, db_column='apellidos')
    dni = models.CharField('DNI', max_length=8, db_column='dni', 
                           validators=[RegexValidator(regex=r'^\d{8}$', message='DNI debe tener 8 dígitos')])
    telefono = models.CharField('Teléfono', max_length=15, null=True, blank=True, db_column='telefono')
    
    # Relaciones FK según BD real
    rol_id = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='usuarios', verbose_name='Rol', db_column='rol_id')
    escuela_id = models.ForeignKey('School', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='usuarios', verbose_name='Escuela', db_column='escuela_id')
    
    # Campos de estado
    activo = models.BooleanField('Activo', default=True, db_column='activo')
    ultimo_acceso = models.DateTimeField('Último Acceso', null=True, blank=True, db_column='ultimo_acceso')
    fecha_creacion = models.DateTimeField('Fecha Creación', auto_now_add=True, db_column='fecha_creacion')
    creado_por = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='usuarios_creados', db_column='creado_por')
    
    # Properties para compatibilidad con código existente
    @property
    def email(self):
        """Alias para compatibilidad con código que usa 'email'."""
        return self.correo
    
    @email.setter
    def email(self, value):
        self.correo = value
    
    @property
    def first_name(self):
        """Alias para compatibilidad."""
        return self.nombres
    
    @first_name.setter
    def first_name(self, value):
        self.nombres = value
    
    @property
    def last_name(self):
        """Alias para compatibilidad."""
        return self.apellidos
    
    @last_name.setter
    def last_name(self, value):
        self.apellidos = value
    
    @property
    def password(self):
        """Alias para compatibilidad."""
        return self.hash_contraseña
    
    @password.setter
    def password(self, value):
        self.hash_contraseña = value
    
    @property
    def is_active(self):
        """Alias para compatibilidad."""
        return self.activo
    
    @is_active.setter
    def is_active(self, value):
        self.activo = value
    
    @property
    def last_login(self):
        """Alias para compatibilidad."""
        return self.ultimo_acceso
    
    @last_login.setter
    def last_login(self, value):
        self.ultimo_acceso = value
    
    @property
    def is_staff(self):
        """
        Determina si el usuario puede acceder al admin de Django.
        Solo ADMINISTRADOR y COORDINADOR tienen acceso al admin.
        """
        if self.rol_id is None:
            return False
        return self.rol_id.nombre in ['ADMINISTRADOR', 'COORDINADOR']
    
    @property
    def is_superuser(self):
        """
        Determina si el usuario es superusuario.
        Solo el rol ADMINISTRADOR tiene todos los permisos.
        """
        if self.rol_id is None:
            return False
        return self.rol_id.nombre == 'ADMINISTRADOR'

    objects = CustomUserManager()

    USERNAME_FIELD = 'correo'  # Cambiado de 'email' a 'correo'
    REQUIRED_FIELDS = ['nombres', 'apellidos', 'dni']

    class Meta:
        db_table = 'upeu_usuario'  # Tabla REAL en PostgreSQL
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        indexes = [
            models.Index(fields=['correo']),
            models.Index(fields=['dni']),
            models.Index(fields=['rol_id']),
            models.Index(fields=['activo']),
        ]
        managed = False  # Django NO gestiona esta tabla (ya existe)

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        """Retorna el nombre completo del usuario."""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        """Retorna el primer nombre del usuario."""
        return self.first_name

    @property
    def is_practicante(self):
        """Verifica si el usuario es PRACTICANTE."""
        return self.rol_id and self.rol_id.nombre == 'PRACTICANTE'

    @property
    def is_supervisor(self):
        """Verifica si el usuario es SUPERVISOR."""
        return self.rol_id and self.rol_id.nombre == 'SUPERVISOR'

    @property
    def is_coordinador(self):
        """Verifica si el usuario es COORDINADOR."""
        return self.rol_id and self.rol_id.nombre == 'COORDINADOR'

    @property
    def is_secretaria(self):
        """Verifica si el usuario es SECRETARIA."""
        return self.rol_id and self.rol_id.nombre == 'SECRETARIA'

    @property
    def is_administrador(self):
        """Verifica si el usuario es ADMINISTRADOR."""
        if self.rol_id is None:
            return False
        return self.rol_id.nombre == 'ADMINISTRADOR'
    
    # ===== MÉTODOS DE PERMISOS =====
    
    def get_all_permissions(self):
        """Obtiene todos los permisos efectivos del usuario (rol + personalizados)."""
        permissions = set()
        
        # 1. Permisos del rol (desde rol_id FK)
        if self.rol_id:
            try:
                role_perms = self.rol_id.get_permissions_codes()
                permissions.update(role_perms)
            except Exception:
                pass
        
        # 2. Permisos personalizados (si existen - tabla UserPermission)
        # 2. Permisos personalizados (si existen - tabla UserPermission)
        try:
            custom_perms = self.custom_permissions.select_related('permission').filter(
                permission__is_active=True
            )
            
            for custom in custom_perms:
                # Verificar si no expiró
                if custom.expires_at and custom.is_expired():
                    continue
                
                if custom.permission_type == 'GRANT':
                    permissions.add(custom.permission.code)
                elif custom.permission_type == 'REVOKE':
                    permissions.discard(custom.permission.code)
        except Exception:
            # No hay permisos personalizados o error al obtenerlos
            pass
        
        return list(permissions)
    
    def has_permission(self, permission_code):
        """Verifica si el usuario tiene un permiso específico."""
        return permission_code in self.get_all_permissions()
    
    def has_any_permission(self, permission_codes):
        """Verifica si el usuario tiene al menos uno de los permisos."""
        user_perms = set(self.get_all_permissions())
        return bool(user_perms.intersection(set(permission_codes)))
    
    def has_all_permissions(self, permission_codes):
        """Verifica si el usuario tiene todos los permisos especificados."""
        user_perms = set(self.get_all_permissions())
        return set(permission_codes).issubset(user_perms)
    
    # ===== MÉTODOS REQUERIDOS POR DJANGO ADMIN =====
    
    def has_perm(self, perm, obj=None):
        """
        Requerido por Django admin.
        Los superusuarios tienen todos los permisos.
        """
        if self.is_superuser:
            return True
        return self.has_permission(perm)
    
    def has_module_perms(self, app_label):
        """
        Requerido por Django admin.
        Los superusuarios y staff tienen acceso a todos los módulos.
        """
        return self.is_staff or self.is_superuser


class Avatar(models.Model):
    """Modelo de Avatar para usuarios por rol."""
    
    ROLE_CHOICES = [
        ('PRACTICANTE', 'Practicante'),
        ('SUPERVISOR', 'Supervisor'),
        ('COORDINADOR', 'Coordinador'),
        ('SECRETARIA', 'Secretaria'),
        ('ADMINISTRADOR', 'Administrador'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    url = models.URLField('URL del Avatar', max_length=500)
    role = models.CharField('Rol', max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField('Activo', default=True)
    created_at = models.DateTimeField('Creado en', auto_now_add=True)

    class Meta:
        db_table = 'avatars'
        verbose_name = 'Avatar'
        verbose_name_plural = 'Avatares'
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"Avatar {self.role} - {self.id}"


# =====================================================
# NOTA: Student obsoleto - Usar StudentProfile
# El modelo Student se mantiene comentado para referencia
# pero StudentProfile es el modelo real que mapea a upeu_perfil_practicante
# =====================================================

# class Student(models.Model):  # COMENTADO - Usar StudentProfile
#     """Modelo de Estudiante - OBSOLETO, usar StudentProfile"""
#     pass


# =====================================================
# EMPRESAS Y SUPERVISORES
# =====================================================

class Company(models.Model):
    """
    Modelo de Empresa - ADAPTADO A BD EXISTENTE upeu_empresa.
    Estructura real PostgreSQL con correo (no email), distrito/provincia/departamento.
    """
    
    # Choices para tamaño_empresa ENUM en PostgreSQL
    TAMAÑO_CHOICES = [
        ('MICRO', 'Microempresa'),
        ('PEQUEÑA', 'Pequeña empresa'),
        ('MEDIANA', 'Mediana empresa'),
        ('GRANDE', 'Gran empresa'),
    ]
    
    # Choices para estado_general ENUM en PostgreSQL
    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('INACTIVO', 'Inactivo'),
        ('SUSPENDIDO', 'Suspendido'),
        ('PENDIENTE', 'Pendiente'),
    ]

    id = models.AutoField(primary_key=True, db_column='id')
    nombre = models.CharField('Nombre', max_length=150, db_column='nombre')
    ruc = models.CharField(
        'RUC', 
        max_length=11, 
        unique=True,
        db_column='ruc',
        validators=[RegexValidator(r'^\d{11}$', 'RUC debe tener 11 dígitos')]
    )
    razon_social = models.CharField('Razón social', max_length=200, blank=True, null=True, 
                                    db_column='razon_social')
    direccion = models.TextField('Dirección', blank=True, null=True, db_column='direccion')
    distrito = models.CharField('Distrito', max_length=50, blank=True, null=True, db_column='distrito')
    provincia = models.CharField('Provincia', max_length=50, blank=True, null=True, db_column='provincia')
    departamento = models.CharField('Departamento', max_length=50, blank=True, null=True, 
                                   db_column='departamento')
    telefono = models.CharField('Teléfono', max_length=15, blank=True, null=True, db_column='telefono')
    correo = models.EmailField('Correo', blank=True, null=True, db_column='correo')
    sitio_web = models.URLField('Sitio Web', max_length=200, blank=True, null=True, db_column='sitio_web')
    sector_economico = models.CharField('Sector económico', max_length=100, blank=True, null=True, 
                                       db_column='sector_economico')
    tamaño_empresa = models.CharField('Tamaño', max_length=20, choices=TAMAÑO_CHOICES, 
                                     blank=True, null=True, db_column='tamaño_empresa')
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, 
                             default='PENDIENTE', db_column='estado')
    
    validado_por = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='empresas_validadas',
        db_column='validado_por'
    )
    fecha_validacion = models.DateTimeField('Fecha de validación', blank=True, null=True, 
                                           db_column='fecha_validacion')
    fecha_registro = models.DateTimeField('Fecha de registro', auto_now_add=True, 
                                         db_column='fecha_registro')

    class Meta:
        db_table = 'upeu_empresa'  # Tabla REAL en PostgreSQL
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nombre']
        managed = False  # Django NO gestiona esta tabla (ya existe)

    def __str__(self):
        return self.nombre
    
    # Propiedades para compatibilidad con código existente
    @property
    def email(self):
        """Alias para correo (compatibilidad)."""
        return self.correo
    
    @email.setter
    def email(self, value):
        """Setter para email (compatibilidad)."""
        self.correo = value
    
    @property
    def nombre_comercial(self):
        """Alias para nombre (compatibilidad)."""
        return self.nombre
    
    @property
    def status(self):
        """Alias para estado (compatibilidad)."""
        return self.estado
    
    @status.setter
    def status(self, value):
        """Setter para status (compatibilidad)."""
        self.estado = value
    
    @property
    def created_at(self):
        """Alias para fecha_registro (compatibilidad)."""
        return self.fecha_registro
    
    @property
    def nombre_para_mostrar(self):
        """Retorna el nombre de la empresa."""
        return self.nombre

    @property
    def puede_recibir_practicantes(self):
        """Verifica si la empresa puede recibir practicantes."""
        return self.estado == 'ACTIVO'


# NOTA: Supervisor ahora está en SupervisorProfile más arriba
# Este modelo Supervisor se elimina porque se usa SupervisorProfile

# class Supervisor(models.Model):  # COMENTADO - Usar SupervisorProfile
#     """Modelo de Supervisor de empresa - USAR SupervisorProfile"""
#     pass


class Practice(models.Model):
    """
    Modelo de Práctica Profesional - ADAPTADO A BD EXISTENTE upeu_practica.
    Estructura real PostgreSQL con practicante_id (no student_id).
    """
    
    # Choices para estado_practica ENUM en PostgreSQL (VALORES REALES)
    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador'),
        ('PENDIENTE', 'Pendiente'),
        ('APROBADO', 'Aprobado'),
        ('EN_PROGRESO', 'En Progreso'),
        ('COMPLETADO', 'Completado'),
        ('RECHAZADO', 'Rechazado'),
        ('CANCELADO', 'Cancelado'),
    ]

    # Choices para modalidad_trabajo ENUM en PostgreSQL
    MODALIDAD_CHOICES = [
        ('PRESENCIAL', 'Presencial'),
        ('REMOTO', 'Remoto'),
        ('HIBRIDO', 'Híbrido'),
    ]

    id = models.AutoField(primary_key=True, db_column='id')
    
    # FK a perfiles y empresa (estructura real)
    practicante = models.ForeignKey(
        'StudentProfile', 
        on_delete=models.CASCADE, 
        related_name='practices',
        db_column='practicante_id'
    )
    empresa = models.ForeignKey(
        'Company', 
        on_delete=models.RESTRICT, 
        related_name='practices',
        db_column='empresa_id'
    )
    supervisor = models.ForeignKey(
        'SupervisorProfile', 
        on_delete=models.RESTRICT, 
        null=True, 
        blank=True, 
        related_name='supervised_practices',
        db_column='supervisor_id'
    )
    
    # Personal académico asignado (FK a User directamente)
    coordinador = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coordinated_practices',
        db_column='coordinador_id',
        verbose_name='Coordinador asignado'
    )
    secretaria = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assisted_practices',
        db_column='secretaria_id',
        verbose_name='Secretaria asignada'
    )
    
    # Información básica
    titulo = models.CharField('Título', max_length=200, db_column='titulo')
    descripcion = models.TextField('Descripción', blank=True, null=True, db_column='descripcion')
    objetivos = models.TextField('Objetivos', blank=True, null=True, db_column='objetivos')
    
    # Fechas
    fecha_inicio = models.DateField('Fecha de inicio', db_column='fecha_inicio')
    fecha_fin = models.DateField('Fecha de fin', db_column='fecha_fin')
    
    # Horas
    horas_totales = models.IntegerField('Horas totales', default=480, db_column='horas_totales',
                                       validators=[MinValueValidator(480)])
    horas_completadas = models.IntegerField('Horas completadas', default=0, 
                                           db_column='horas_completadas',
                                           validators=[MinValueValidator(0)])
    
    # Modalidad
    modalidad = models.CharField('Modalidad', max_length=20, choices=MODALIDAD_CHOICES, 
                                default='PRESENCIAL', db_column='modalidad')
    
    # Remuneración
    remunerada = models.BooleanField('Remunerada', default=False, db_column='remunerada')
    monto_remuneracion = models.DecimalField(
        'Monto de remuneración',
        max_digits=10,
        decimal_places=2,
        default=0,
        db_column='monto_remuneracion',
        validators=[MinValueValidator(0)]
    )
    
    # Estado
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, 
                             default='BORRADOR', db_column='estado')
    
    # Metadatos
    fecha_creacion = models.DateTimeField('Fecha Creación', auto_now_add=True, 
                                         db_column='fecha_creacion')
    fecha_actualizacion = models.DateTimeField('Fecha Actualización', auto_now=True, 
                                              db_column='fecha_actualizacion')
    observaciones = models.TextField('Observaciones', blank=True, null=True, db_column='observaciones')

    class Meta:
        db_table = 'upeu_practica'  # Tabla REAL en PostgreSQL
        verbose_name = 'Práctica'
        verbose_name_plural = 'Prácticas'
        ordering = ['-fecha_creacion']
        managed = False  # Django NO gestiona esta tabla (ya existe)

    def __str__(self):
        return f"{self.titulo} - {self.practicante.codigo}"
    
    # Propiedades para compatibilidad con código existente
    @property
    def student(self):
        """Alias para practicante (compatibilidad)."""
        return self.practicante
    
    @property
    def company(self):
        """Alias para empresa (compatibilidad)."""
        return self.empresa
    
    @property
    def status(self):
        """Alias para estado (compatibilidad)."""
        return self.estado
    
    @status.setter
    def status(self, value):
        """Setter para status (compatibilidad)."""
        self.estado = value
    
    @property
    def created_at(self):
        """Alias para fecha_creacion (compatibilidad)."""
        return self.fecha_creacion
    
    @property
    def updated_at(self):
        """Alias para fecha_actualizacion (compatibilidad)."""
        return self.fecha_actualizacion
    
    @property
    def horas_requeridas(self):
        """Alias para horas_totales (compatibilidad)."""
        return self.horas_totales
    
    @property
    def duracion_dias(self):
        """Retorna la duración en días."""
        if self.fecha_inicio and self.fecha_fin:
            return (self.fecha_fin - self.fecha_inicio).days
        return 0

    @property
    def esta_activa(self):
        """Verifica si la práctica está activa."""
        return self.estado == 'EN_CURSO'
    
    @property
    def progreso_porcentaje(self):
        """Calcula el porcentaje de progreso."""
        if self.horas_totales > 0:
            return min((self.horas_completadas / self.horas_totales) * 100, 100)
        return 0
    
    @property
    def porcentaje_completado(self):
        """Retorna el porcentaje de horas completadas."""
        if self.horas_requeridas > 0:
            return (self.horas_completadas / self.horas_requeridas) * 100
        return 0
    
    def save(self, *args, **kwargs):
        """Override save para registrar cambios de estado."""
        # Detectar si cambió el estado
        if self.pk:
            try:
                old_practice = Practice.objects.get(pk=self.pk)
                if old_practice.status != self.status:
                    # Registrar en historial después de guardar
                    self._status_changed = True
                    self._old_status = old_practice.status
                    self._new_status = self.status
            except Practice.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Crear registro de historial si cambió el estado
        if hasattr(self, '_status_changed') and self._status_changed:
            from src.adapters.secondary.database.models import PracticeStatusHistory
            PracticeStatusHistory.objects.create(
                practice=self,
                estado_anterior=self._old_status,
                estado_nuevo=self._new_status
            )


class Document(models.Model):
    """Modelo de Documento."""
    
    TIPO_CHOICES = [
        ('PRACTICE_AGREEMENT', 'Convenio de práctica'),
        ('EVALUATION_REPORT', 'Reporte de evaluación'),
        ('FINAL_REPORT', 'Reporte final'),
        ('COMPANY_VALIDATION', 'Validación de empresa'),
        ('STUDENT_CV', 'CV del estudiante'),
        ('ACADEMIC_RECORD', 'Récord académico'),
        ('MONTHLY_REPORT', 'Reporte mensual'),
        ('PRACTICE_PLAN', 'Plan de práctica'),
        ('OTHER', 'Otro'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente de revisión'),
        ('VALIDATED', 'Validado'),
        ('REJECTED', 'Rechazado'),
        ('OBSERVED', 'Observado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    practice = models.ForeignKey(Practice, on_delete=models.CASCADE, related_name='documents')
    tipo = models.CharField('Tipo', max_length=30, choices=TIPO_CHOICES)
    nombre_archivo = models.CharField('Nombre del archivo', max_length=255)
    archivo = models.FileField('Archivo', upload_to='documents/%Y/%m/')
    tamaño_bytes = models.PositiveIntegerField('Tamaño en bytes')
    mime_type = models.CharField('Tipo MIME', max_length=100)
    
    # Usuario que subió
    subido_por = models.ForeignKey('User', on_delete=models.CASCADE, related_name='uploaded_documents')
    
    # Estado del documento
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Aprobación/Validación (deprecated, usar status)
    aprobado = models.BooleanField('Aprobado', default=False)
    fecha_aprobacion = models.DateTimeField('Fecha de aprobación', blank=True, null=True)
    aprobado_por = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_documents')
    
    # Validación
    validated_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validated_documents',
        verbose_name='Validado por'
    )
    validation_date = models.DateTimeField('Fecha de validación', null=True, blank=True)
    observations = models.TextField('Observaciones', blank=True, null=True)
    
    # Versionado
    version = models.PositiveIntegerField('Versión', default=1)
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='newer_versions',
        verbose_name='Versión anterior'
    )
    
    created_at = models.DateTimeField('Creado en', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado en', auto_now=True)

    class Meta:
        db_table = 'documents'
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        indexes = [
            models.Index(fields=['practice']),
            models.Index(fields=['tipo']),
            models.Index(fields=['status']),
            models.Index(fields=['aprobado']),
            models.Index(fields=['version']),
        ]

    def __str__(self):
        return f"{self.nombre_archivo} v{self.version} - {self.practice.titulo}"
    
    def validate(self, user):
        """Valida el documento."""
        self.status = 'VALIDATED'
        self.validated_by = user
        self.validation_date = timezone.now()
        self.aprobado = True  # Para compatibilidad
        self.aprobado_por = user
        self.fecha_aprobacion = timezone.now()
        self.save()
    
    def reject(self, user, observations=''):
        """Rechaza el documento."""
        self.status = 'REJECTED'
        self.validated_by = user
        self.validation_date = timezone.now()
        self.observations = observations
        self.save()

    @property
    def tamaño_legible(self):
        """Retorna el tamaño en formato legible."""
        if self.tamaño_bytes < 1024:
            return f"{self.tamaño_bytes} B"
        elif self.tamaño_bytes < 1024 * 1024:
            return f"{self.tamaño_bytes / 1024:.1f} KB"
        else:
            return f"{self.tamaño_bytes / (1024 * 1024):.1f} MB"

    @property
    def es_imagen(self):
        """Verifica si es una imagen."""
        return self.mime_type.startswith('image/')

    @property
    def es_pdf(self):
        """Verifica si es un PDF."""
        return self.mime_type == 'application/pdf'


class Notification(models.Model):
    """Modelo de Notificación - Mapea a tabla `notifications`."""
    
    TIPO_CHOICES = [
        ('INFO', 'Información'),
        ('SUCCESS', 'Éxito'),
        ('WARNING', 'Advertencia'),
        ('ERROR', 'Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False, db_column='id')
    user_id = models.UUIDField('ID de Usuario', db_column='user_id')  # UUID en tabla notifications
    titulo = models.CharField('Título', max_length=200, db_column='titulo')
    mensaje = models.TextField('Mensaje', db_column='mensaje')
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES, default='INFO', db_column='tipo')
    leida = models.BooleanField('Leída', default=False, db_column='leida')
    fecha_lectura = models.DateTimeField('Fecha de lectura', blank=True, null=True, db_column='fecha_lectura')
    accion_url = models.URLField('URL de acción', blank=True, null=True, db_column='accion_url')
    created_at = models.DateTimeField('Creado en', auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField('Actualizado en', auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'notifications'  # Tabla REAL en PostgreSQL
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-created_at']
        managed = False  # Django NO gestiona esta tabla
        indexes = [
            models.Index(fields=['user_id', 'leida']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.titulo} - Usuario {self.user_id}"

    @property
    def es_importante(self):
        """Verifica si la notificación es importante."""
        return self.tipo in ['WARNING', 'ERROR']
    
    @property
    def user(self):
        """Obtiene el usuario relacionado (lazy loading)."""
        if not hasattr(self, '_user_cache'):
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                self._user_cache = User.objects.get(id=self.user_id)
            except User.DoesNotExist:
                self._user_cache = None
        return self._user_cache


# OpaqueSession y SessionActivity eliminados - Sistema JWT PURO
# Estos modelos ya no son necesarios porque usamos JWT PURO con blacklist


# ===== SISTEMA DE ROLES Y PERMISOS =====

# ===============================================
# NOTA: Permission, RolePermission y UserPermission
# NO EXISTEN en la BD real de PostgreSQL.
# Los permisos están en upeu_rol.permisos como JSONB.
# Se comentan estos modelos obsoletos.
# ===============================================

# class Permission(models.Model):  # COMENTADO - No existe en BD real
#     """Permisos disponibles en el sistema - NO EXISTE EN BD REAL"""
#     id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
#     code = models.CharField('Código', max_length=100, unique=True, db_index=True)
#     name = models.CharField('Nombre', max_length=200)
#     description = models.TextField('Descripción', blank=True, null=True)
#     module = models.CharField('Módulo', max_length=100, blank=True, null=True)
#     is_active = models.BooleanField('Activo', default=True)
#     created_at = models.DateTimeField('Creado en', auto_now_add=True)
#     
#     class Meta:
#         db_table = 'permissions'
#         verbose_name = 'Permiso'
#         verbose_name_plural = 'Permisos'
#         ordering = ['module', 'code']
#     
#     def __str__(self):
#         return f"{self.code} - {self.name}"


class Role(models.Model):
    """
    Roles del sistema - ADAPTADO A BD EXISTENTE upeu_rol.
    Estructura real PostgreSQL:
    - nombre (tipo_rol ENUM, no code)
    - descripcion
    - permisos (JSONB, no tabla separada)
    - fecha_creacion
    
    NOTA: Los permisos están almacenados como JSONB en la columna 'permisos',
    NO como tabla separada Permission/RolePermission.
    """
    
    # Choices para tipo_rol enum de PostgreSQL
    TIPO_ROL_CHOICES = [
        ('ADMINISTRADOR', 'Administrador'),
        ('COORDINADOR', 'Coordinador'),
        ('SECRETARIA', 'Secretaria'),
        ('SUPERVISOR', 'Supervisor'),
        ('PRACTICANTE', 'Practicante'),
    ]
    
    id = models.AutoField(primary_key=True, db_column='id')
    nombre = models.CharField('Nombre (tipo_rol)', max_length=20, unique=True, 
                              choices=TIPO_ROL_CHOICES, db_column='nombre')
    descripcion = models.TextField('Descripción', blank=True, null=True, db_column='descripcion')
    
    # Permisos como JSONB (estructura real de BD)
    permisos = models.JSONField('Permisos', default=dict, blank=True, db_column='permisos',
                               help_text='Estructura JSON con permisos del rol. Ej: {"practices": ["view", "create"], "students": ["view"]}')
    
    fecha_creacion = models.DateTimeField('Fecha Creación', auto_now_add=True, db_column='fecha_creacion')
    
    class Meta:
        db_table = 'upeu_rol'  # Tabla REAL en PostgreSQL
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['nombre']
        managed = False  # Django NO gestiona esta tabla (ya existe)
    
    def __str__(self):
        return self.get_nombre_display()

    # Compatibilidad: exponer 'code' y 'description' esperados por código antiguo
    @property
    def code(self):
        return self.nombre

    @property
    def description(self):
        return self.descripcion

    @property
    def name(self):
        return self.nombre
    
    @property
    def permissions(self):
        """Retorna permisos desde el JSONB (no hay tabla relacional para upeu_rol)."""
        return []  # El sistema legacy usa permisos JSONB, no tabla Permission
    
    def get_permissions_codes(self):
        """Obtiene lista de códigos de permisos del rol desde JSONB."""
        if not isinstance(self.permisos, dict):
            return []
        
        permissions = []
        for module, actions in self.permisos.items():
            if isinstance(actions, list):
                permissions.extend([f"{module}.{action}" for action in actions])
            elif module == "all" and actions is True:
                permissions.append("all")
        return permissions
    
    def has_permission(self, permission_code):
        """Verifica si el rol tiene un permiso específico."""
        # Si tiene permiso 'all', tiene todos
        if self.permisos.get('all') is True:
            return True
        
        # Verificar permiso específico
        try:
            module, action = permission_code.split('.', 1)
            module_permissions = self.permisos.get(module, [])
            return action in module_permissions if isinstance(module_permissions, list) else False
        except (ValueError, AttributeError):
            return False
    
    def add_permission(self, permission_code):
        """Agrega un permiso al JSONB."""
        try:
            module, action = permission_code.split('.', 1)
            if module not in self.permisos:
                self.permisos[module] = []
            if isinstance(self.permisos[module], list) and action not in self.permisos[module]:
                self.permisos[module].append(action)
                self.save()
        except ValueError:
            pass


# ===============================================
# NOTA: Permission, RolePermission y UserPermission
# NO EXISTEN en la BD real de PostgreSQL.
# Los permisos están en upeu_rol.permisos como JSONB.
# Se eliminan o comentan estos modelos.
# ===============================================

# class Permission(models.Model):  # COMENTADO - No existe en BD real
#     """Permisos granulares del sistema - NO EXISTE EN BD REAL"""
#     pass

# class RolePermission(models.Model):  # COMENTADO - No existe en BD real
#     """Relación entre Roles y Permisos - NO EXISTE EN BD REAL"""
#     pass

# class UserPermission(models.Model):  # COMENTADO - No existe en BD real
#     """Permisos personalizados por usuario - NO EXISTE EN BD REAL"""
#     pass


# =====================================================
# PERFILES DE USUARIO (Arquitectura separada de BD real)
# =====================================================

class StudentProfile(models.Model):
    """
    Perfil de Practicante/Estudiante - ADAPTADO A upeu_perfil_practicante.
    Cada usuario con rol PRACTICANTE tiene un registro aquí.
    """
    ESTADO_ACADEMICO_CHOICES = [
        ('REGULAR', 'Regular'),
        ('IRREGULAR', 'Irregular'),
        ('INACTIVO', 'Inactivo'),
        ('EGRESADO', 'Egresado'),
    ]
    
    id = models.AutoField(primary_key=True, db_column='id')
    usuario = models.OneToOneField(
        'User', 
        on_delete=models.CASCADE, 
        related_name='student_profile',
        db_column='usuario_id'
    )
    codigo = models.CharField('Código Estudiante', max_length=10, unique=True, db_column='codigo')
    semestre = models.IntegerField('Semestre', db_column='semestre',
                                   validators=[MinValueValidator(1), MaxValueValidator(12)])
    promedio = models.DecimalField('Promedio', max_digits=4, decimal_places=2, db_column='promedio',
                                   validators=[MinValueValidator(0), MaxValueValidator(20)])
    fecha_nacimiento = models.DateField('Fecha Nacimiento', db_column='fecha_nacimiento')
    direccion = models.TextField('Dirección', blank=True, null=True, db_column='direccion')
    
    escuela = models.ForeignKey(
        'School', 
        on_delete=models.RESTRICT, 
        related_name='students',
        db_column='escuela_id',
        blank=True,
        null=True
    )
    rama = models.ForeignKey(
        'Branch', 
        on_delete=models.RESTRICT, 
        related_name='students',
        db_column='rama_id',
        blank=True,
        null=True
    )
    
    cv_path = models.CharField('Ruta CV', max_length=255, blank=True, null=True, db_column='cv_path')
    fecha_cv_subido = models.DateTimeField('Fecha CV Subido', blank=True, null=True, db_column='fecha_cv_subido')
    estado_academico = models.CharField('Estado Académico', max_length=20, 
                                       choices=ESTADO_ACADEMICO_CHOICES,
                                       default='REGULAR', db_column='estado_academico')
    fecha_creacion = models.DateTimeField('Fecha Creación', auto_now_add=True, db_column='fecha_creacion')
    
    class Meta:
        db_table = 'upeu_perfil_practicante'
        verbose_name = 'Perfil Practicante'
        verbose_name_plural = 'Perfiles Practicantes'
        managed = False
    
    def __str__(self):
        return f"{self.codigo} - {self.usuario.get_full_name()}"
    
    @property
    def edad(self):
        """Calcula edad del estudiante."""
        from datetime import date
        today = date.today()
        return today.year - self.fecha_nacimiento.year - (
            (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )


class SupervisorProfile(models.Model):
    """
    Perfil de Supervisor de Empresa - ADAPTADO A upeu_perfil_supervisor.
    Cada usuario con rol SUPERVISOR tiene un registro aquí.
    """
    id = models.AutoField(primary_key=True, db_column='id')
    usuario = models.OneToOneField(
        'User', 
        on_delete=models.CASCADE, 
        related_name='supervisor_profile',
        db_column='usuario_id'
    )
    empresa = models.ForeignKey(
        'Company', 
        on_delete=models.CASCADE, 
        related_name='supervisors',
        db_column='empresa_id'
    )
    cargo = models.CharField('Cargo', max_length=100, db_column='cargo')
    telefono_trabajo = models.CharField('Teléfono Trabajo', max_length=15, blank=True, null=True, 
                                       db_column='telefono_trabajo')
    correo_trabajo = models.EmailField('Correo Trabajo', blank=True, null=True, db_column='correo_trabajo')
    años_experiencia = models.IntegerField('Años Experiencia', default=0, db_column='años_experiencia',
                                          validators=[MinValueValidator(0)])
    especialidad = models.CharField('Especialidad', max_length=100, blank=True, null=True, 
                                   db_column='especialidad')
    fecha_creacion = models.DateTimeField('Fecha Creación', auto_now_add=True, db_column='fecha_creacion')
    
    class Meta:
        db_table = 'upeu_perfil_supervisor'
        verbose_name = 'Perfil Supervisor'
        verbose_name_plural = 'Perfiles Supervisores'
        managed = False
    
    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.cargo} ({self.empresa.nombre})"


class CoordinatorSchool(models.Model):
    """
    Coordinador de Escuela - ADAPTADO A upeu_coordinador_escuela.
    Relación entre usuario COORDINADOR y escuela asignada.
    """
    id = models.AutoField(primary_key=True, db_column='id')
    usuario = models.ForeignKey(
        'User', 
        on_delete=models.CASCADE, 
        related_name='coordinator_assignments',
        db_column='usuario_id'
    )
    escuela = models.ForeignKey(
        'School', 
        on_delete=models.CASCADE, 
        related_name='coordinators',
        db_column='escuela_id'
    )
    fecha_asignacion = models.DateField('Fecha Asignación', auto_now_add=True, db_column='fecha_asignacion')
    fecha_fin = models.DateField('Fecha Fin', blank=True, null=True, db_column='fecha_fin')
    activo = models.BooleanField('Activo', default=True, db_column='activo')
    
    class Meta:
        db_table = 'upeu_coordinador_escuela'
        verbose_name = 'Coordinador de Escuela'
        verbose_name_plural = 'Coordinadores de Escuelas'
        unique_together = [['usuario', 'escuela', 'activo']]
        managed = False
    
    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.escuela.nombre}"


class SecretariaProfile(models.Model):
    """
    Perfil de Secretaria - ADAPTADO A upeu_perfil_secretaria.
    Cada usuario con rol SECRETARIA tiene un registro aquí.
    """
    id = models.AutoField(primary_key=True, db_column='id')
    usuario = models.OneToOneField(
        'User', 
        on_delete=models.CASCADE, 
        related_name='secretaria_profile',
        db_column='usuario_id'
    )
    escuela = models.ForeignKey(
        'School', 
        on_delete=models.RESTRICT, 
        related_name='secretarias',
        db_column='escuela_id',
        blank=True,
        null=True
    )
    fecha_asignacion = models.DateField('Fecha Asignación', auto_now_add=True, db_column='fecha_asignacion')
    permisos_especiales = models.JSONField('Permisos Especiales', default=dict, blank=True, 
                                          db_column='permisos_especiales')
    
    class Meta:
        db_table = 'upeu_perfil_secretaria'
        verbose_name = 'Perfil Secretaria'
        verbose_name_plural = 'Perfiles Secretarias'
        managed = False
    
    def __str__(self):
        return f"{self.usuario.get_full_name()} - Secretaria"


class AdminProfile(models.Model):
    """
    Perfil de Administrador - ADAPTADO A upeu_perfil_admin.
    Cada usuario con rol ADMINISTRADOR tiene un registro aquí.
    """
    id = models.AutoField(primary_key=True, db_column='id')
    usuario = models.OneToOneField(
        'User', 
        on_delete=models.CASCADE, 
        related_name='admin_profile',
        db_column='usuario_id'
    )
    nivel_acceso = models.IntegerField('Nivel Acceso', default=1, db_column='nivel_acceso',
                                      validators=[MinValueValidator(1), MaxValueValidator(5)])
    fecha_asignacion = models.DateField('Fecha Asignación', auto_now_add=True, db_column='fecha_asignacion')
    
    class Meta:
        db_table = 'upeu_perfil_admin'
        verbose_name = 'Perfil Administrador'
        verbose_name_plural = 'Perfiles Administradores'
        managed = False
    
    def __str__(self):
        return f"{self.usuario.get_full_name()} - Admin (Nivel {self.nivel_acceso})"


class SuperAdminProfile(models.Model):
    """
    Perfil de Super Administrador - ADAPTADO A upeu_perfil_superadmin.
    Cada usuario con rol SUPERADMIN tiene un registro aquí.
    """
    id = models.AutoField(primary_key=True, db_column='id')
    usuario = models.OneToOneField(
        'User', 
        on_delete=models.CASCADE, 
        related_name='superadmin_profile',
        db_column='usuario_id'
    )
    fecha_asignacion = models.DateField('Fecha Asignación', auto_now_add=True, db_column='fecha_asignacion')
    permisos_totales = models.BooleanField('Permisos Totales', default=True, db_column='permisos_totales')
    
    class Meta:
        db_table = 'upeu_perfil_superadmin'
        verbose_name = 'Perfil Super Administrador'
        verbose_name_plural = 'Perfiles Super Administradores'
        managed = False
    
    def __str__(self):
        return f"{self.usuario.get_full_name()} - SuperAdmin"


# =====================================================
# MODELOS ACADÉMICOS
# =====================================================

class School(models.Model):
    """
    Escuela Profesional / Carrera - ADAPTADO A BD EXISTENTE upeu_escuela.
    Estructura real PostgreSQL sin coordinador FK, con estado enum.
    """
    
    # Choices para estado_general ENUM en PostgreSQL
    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('INACTIVO', 'Inactivo'),
        ('SUSPENDIDO', 'Suspendido'),
        ('PENDIENTE', 'Pendiente'),
    ]
    
    id = models.AutoField(primary_key=True, db_column='id')
    nombre = models.CharField('Nombre', max_length=100, db_column='nombre')
    codigo = models.CharField('Código', max_length=10, unique=True, db_column='codigo')
    descripcion = models.TextField('Descripción', blank=True, null=True, db_column='descripcion')
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, 
                             default='ACTIVO', db_column='estado')
    fecha_creacion = models.DateTimeField('Fecha Creación', auto_now_add=True, 
                                         db_column='fecha_creacion')
    
    class Meta:
        db_table = 'upeu_escuela'  # Tabla REAL en PostgreSQL
        verbose_name = 'Escuela Profesional'
        verbose_name_plural = 'Escuelas Profesionales'
        ordering = ['codigo']
        managed = False  # Django NO gestiona esta tabla (ya existe)
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    # Compatibilidad con API legacy
    @property
    def code(self):
        return self.codigo

    @property
    def name(self):
        return self.nombre

    @property
    def description(self):
        return self.descripcion
    
    # Propiedades para compatibilidad con código existente
    @property
    def activa(self):
        """Alias para estado (compatibilidad)."""
        return self.estado == 'ACTIVO'
    
    @property
    def created_at(self):
        """Alias para fecha_creacion (compatibilidad)."""
        return self.fecha_creacion
    
    @property
    def updated_at(self):
        """Alias para fecha_creacion (compatibilidad - no hay updated_at en BD)."""
        return self.fecha_creacion
    
    @property
    def total_estudiantes(self):
        """Retorna el total de estudiantes en la escuela."""
        return self.students.count()


# ------------------------------------------------------------------
# Backwards compatibility aliases
# Algunos módulos importan `Student` o `Supervisor` del módulo de modelos.
# Como migramos a perfiles (`StudentProfile`, `SupervisorProfile`),
# mantenemos alias para evitar tener que cambiar cientos de imports.
# ------------------------------------------------------------------
try:
    Student = globals().get('StudentProfile') or None
except Exception:
    Student = None

try:
    Supervisor = globals().get('SupervisorProfile') or None


    # ------------------------------------------------------------------
    # Compatibilidad: modelos mínimos para permisos (mapear a tablas reales)
    # Se definen como managed=False para no obligar a migraciones.
    # ------------------------------------------------------------------
    class Permission(models.Model):
        """Modelo que mapea a tabla `permissions` (tabla real en BD)."""
        id = models.AutoField(primary_key=True, db_column='id')
        codigo = models.CharField('Código', max_length=100, unique=True, db_column='code')
        nombre = models.CharField('Nombre', max_length=200, db_column='name')
        descripcion = models.TextField('Descripción', blank=True, null=True, db_column='description')
        module = models.CharField('Módulo', max_length=100, blank=True, null=True, db_column='module')
        is_active = models.BooleanField('Activo', default=True, db_column='is_active')
        created_at = models.DateTimeField('Creado en', auto_now_add=True, db_column='created_at')

        class Meta:
            db_table = 'permissions'  # Tabla REAL en PostgreSQL
            verbose_name = 'Permiso'
            verbose_name_plural = 'Permisos'
            managed = False

        def __str__(self):
            return f"{self.codigo} - {self.nombre}"
        
        # Properties para compatibilidad con código existente
        @property
        def code(self):
            """Alias para codigo."""
            return self.codigo
        
        @property
        def name(self):
            """Alias para nombre."""
            return self.nombre
        
        @property
        def description(self):
            """Alias para descripcion."""
            return self.descripcion


    # ===== SISTEMA NUEVO: ROLES Y PERMISOS CON UUID =====

    class RoleNew(models.Model):
        """
        Sistema NUEVO de roles - Tabla 'roles' con UUIDs.
        Roles dinámicos con permisos relacionales (tabla role_permissions).
        """
        id = models.UUIDField(primary_key=True, default=uuid4, editable=False, db_column='id')
        code = models.CharField('Código', max_length=50, unique=True, db_column='code')
        name = models.CharField('Nombre', max_length=100, db_column='name')
        description = models.TextField('Descripción', blank=True, null=True, db_column='description')
        is_active = models.BooleanField('Activo', default=True, db_column='is_active')
        is_system = models.BooleanField('Es del sistema', default=False, db_column='is_system')
        created_at = models.DateTimeField('Creado en', auto_now_add=True, db_column='created_at')
        updated_at = models.DateTimeField('Actualizado en', auto_now=True, db_column='updated_at')
        
        permissions = models.ManyToManyField('Permission', through='RolePermission', related_name='new_roles')

        class Meta:
            db_table = 'roles'
            verbose_name = 'Rol Nuevo'
            verbose_name_plural = 'Roles Nuevos'
            ordering = ['name']
            managed = False

        def __str__(self):
            return f"{self.code} - {self.name}"


    class RolePermission(models.Model):
        """Relación entre roles nuevos y permisos (tabla role_permissions con UUIDs)."""
        id = models.UUIDField(primary_key=True, default=uuid4, editable=False, db_column='id')
        rol = models.ForeignKey('RoleNew', on_delete=models.CASCADE, db_column='role_id', related_name='role_perm_map')
        permiso = models.ForeignKey('Permission', on_delete=models.CASCADE, db_column='permission_id', related_name='role_perm_map')
        granted_at = models.DateTimeField('Otorgado en', auto_now_add=True, db_column='granted_at')
        granted_by_id = models.UUIDField('Otorgado por', blank=True, null=True, db_column='granted_by_id')

        class Meta:
            db_table = 'role_permissions'  # Tabla REAL en PostgreSQL
            verbose_name = 'Permiso de Rol'
            verbose_name_plural = 'Permisos de Roles'
            managed = False
            unique_together = [['rol', 'permiso']]

        def __str__(self):
            return f"{self.rol.code} - {self.permiso.code}"

        # Compatibilidad con código legacy
        @property
        def role(self):
            return self.rol
        
        @property
        def permission(self):
            return self.permiso


    class UserPermission(models.Model):
        """Permisos personalizados por usuario (tabla user_permissions con UUIDs)."""
        id = models.UUIDField(primary_key=True, default=uuid4, editable=False, db_column='id')
        usuario = models.ForeignKey('User', on_delete=models.CASCADE, db_column='user_id', related_name='user_perm_map')
        permiso = models.ForeignKey('Permission', on_delete=models.CASCADE, db_column='permission_id', related_name='user_perm_map')
        permiso_tipo = models.CharField('Tipo', max_length=10, blank=True, null=True, db_column='permission_type')
        granted_at = models.DateTimeField('Otorgado en', blank=True, null=True, db_column='granted_at')
        expires_at = models.DateTimeField('Expira en', blank=True, null=True, db_column='expires_at')
        otorgado_por = models.ForeignKey('User', on_delete=models.SET_NULL, blank=True, null=True, 
                                        db_column='granted_by_id', related_name='permissions_granted')

        class Meta:
            db_table = 'user_permissions'  # Tabla REAL en PostgreSQL
            verbose_name = 'Permiso de Usuario'
            verbose_name_plural = 'Permisos de Usuarios'
            managed = False

        def __str__(self):
            return f"{self.usuario.correo} - {self.permiso.code} ({self.permiso_tipo})"
        
        # Properties para compatibilidad
        @property
        def permission_type(self):
            return self.permiso_tipo
        
        @property
        def user(self):
            return self.usuario
        
        @property
        def permission(self):
            return self.permiso
        
        @property
        def granted_by(self):
            return self.otorgado_por
except Exception:
    Supervisor = None



class Branch(models.Model):
    """
    Rama o especialidad - ADAPTADO A BD EXISTENTE upeu_rama.
    Estructura real PostgreSQL con escuela_id FK.
    """
    
    id = models.AutoField(primary_key=True, db_column='id')
    nombre = models.CharField('Nombre', max_length=100, db_column='nombre')
    descripcion = models.TextField('Descripción', blank=True, null=True, db_column='descripcion')
    escuela = models.ForeignKey(
        'School', 
        on_delete=models.CASCADE, 
        related_name='branches',
        db_column='escuela_id'
    )
    activa = models.BooleanField('Activa', default=True, db_column='activa')
    fecha_creacion = models.DateTimeField('Fecha Creación', auto_now_add=True, 
                                         db_column='fecha_creacion')
    
    class Meta:
        db_table = 'upeu_rama'  # Tabla REAL en PostgreSQL
        verbose_name = 'Rama/Especialidad'
        verbose_name_plural = 'Ramas/Especialidades'
        ordering = ['nombre']
        managed = False  # Django NO gestiona esta tabla (ya existe)
    
    def __str__(self):
        return f"{self.escuela.codigo} - {self.nombre}"
    
    # Propiedades para compatibilidad con código existente
    @property
    def school(self):
        """Alias para escuela (compatibilidad)."""
        return self.escuela
    
    @property
    def created_at(self):
        """Alias para fecha_creacion (compatibilidad)."""
        return self.fecha_creacion
    
    @property
    def updated_at(self):
        """Alias para fecha_creacion (compatibilidad - no hay updated_at en BD)."""
        return self.fecha_creacion
    
    @property
    def total_estudiantes(self):
        """Retorna el total de estudiantes en la rama."""
        return self.students.count()


# =====================================================
# EVALUACIONES Y SEGUIMIENTO
# =====================================================

class PracticeEvaluation(models.Model):
    """
    Evaluación de práctica profesional - ADAPTADO A BD EXISTENTE upeu_evaluacion_practica.
    Estructura real PostgreSQL simplificada sin status ni campos de aprobación.
    """
    
    TIPO_EVALUADOR_CHOICES = [
        ('SUPERVISOR', 'Supervisor de empresa'),
        ('COORDINADOR', 'Coordinador académico'),
    ]
    
    PERIODO_CHOICES = [
        ('INICIAL', 'Evaluación inicial'),
        ('MENSUAL_1', 'Evaluación mensual 1'),
        ('MENSUAL_2', 'Evaluación mensual 2'),
        ('MENSUAL_3', 'Evaluación mensual 3'),
        ('FINAL', 'Evaluación final'),
    ]
    
    id = models.AutoField(primary_key=True, db_column='id')
    practica = models.ForeignKey(
        'Practice', 
        on_delete=models.CASCADE, 
        related_name='evaluations',
        db_column='practica_id'
    )
    evaluador = models.ForeignKey(
        'User', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='evaluations_made',
        db_column='evaluador_id'
    )
    tipo_evaluador = models.CharField('Tipo de evaluador', max_length=20, 
                                     choices=TIPO_EVALUADOR_CHOICES, 
                                     default='SUPERVISOR',
                                     db_column='tipo_evaluador')
    periodo_evaluacion = models.CharField('Periodo', max_length=50, choices=PERIODO_CHOICES,
                                         blank=True, null=True,
                                         db_column='periodo_evaluacion')
    
    # Criterios de evaluación (JSONB)
    criterios_evaluacion = models.JSONField(
        'Criterios de evaluación',
        default=dict,
        help_text='JSON con criterios específicos y puntajes',
        blank=True,
        db_column='criterios_evaluacion'
    )
    
    # Puntaje
    puntaje_total = models.DecimalField(
        'Puntaje total',
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Puntaje de 0 a 100',
        blank=True,
        null=True,
        db_column='puntaje_total'
    )
    
    # Comentarios
    comentarios = models.TextField('Comentarios', blank=True, null=True, db_column='comentarios')
    recomendaciones = models.TextField('Recomendaciones', blank=True, null=True, 
                                      db_column='recomendaciones')
    
    # Auditoría
    fecha_evaluacion = models.DateTimeField('Fecha de evaluación', auto_now_add=True,
                                           db_column='fecha_evaluacion')
    
    class Meta:
        db_table = 'upeu_evaluacion_practica'  # Tabla REAL en PostgreSQL
        verbose_name = 'Evaluación de Práctica'
        verbose_name_plural = 'Evaluaciones de Prácticas'
        ordering = ['-fecha_evaluacion']
        managed = False  # Django NO gestiona esta tabla (ya existe)
    
    def __str__(self):
        return f"{self.practica.titulo} - {self.periodo_evaluacion} ({self.puntaje_total})"
    
    # Propiedades para compatibilidad con código existente
    @property
    def practice(self):
        """Alias para practica (compatibilidad)."""
        return self.practica
    
    @property
    def evaluator(self):
        """Alias para evaluador (compatibilidad)."""
        return self.evaluador
    
    @property
    def created_at(self):
        """Alias para fecha_evaluacion (compatibilidad)."""
        return self.fecha_evaluacion
    
    @property
    def updated_at(self):
        """Alias para fecha_evaluacion (compatibilidad - no hay updated_at en BD)."""
        return self.fecha_evaluacion
    
    @property
    def status(self):
        """Compatibilidad - siempre APPROVED (no hay status en BD real)."""
        return 'APPROVED'
    
    @property
    def calificacion_vigesimal(self):
        """Convierte puntaje de 0-100 a escala vigesimal (0-20)."""
        if self.puntaje_total:
            return (self.puntaje_total / 100) * 20
        return 0
    
    def approve(self, user):
        """Aprueba la evaluación."""
        self.status = 'APPROVED'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()


class PracticeStatusHistory(models.Model):
    """Historial de cambios de estado de prácticas."""
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    practice = models.ForeignKey(Practice, on_delete=models.CASCADE, related_name='status_history')
    estado_anterior = models.CharField('Estado anterior', max_length=50, blank=True, null=True)
    estado_nuevo = models.CharField('Estado nuevo', max_length=50)
    usuario_responsable = models.ForeignKey(
        'User', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='practice_status_changes'
    )
    motivo = models.TextField('Motivo del cambio', blank=True, null=True)
    metadata = models.JSONField('Metadata adicional', default=dict, blank=True)
    fecha_cambio = models.DateTimeField('Fecha de cambio', auto_now_add=True)
    
    class Meta:
        db_table = 'practice_status_history'
        verbose_name = 'Historial de Estado de Práctica'
        verbose_name_plural = 'Historiales de Estados de Prácticas'
        ordering = ['-fecha_cambio']
        indexes = [
            models.Index(fields=['practice']),
            models.Index(fields=['estado_nuevo']),
            models.Index(fields=['fecha_cambio']),
        ]
    
    def __str__(self):
        return f"{self.practice.titulo}: {self.estado_anterior} → {self.estado_nuevo}"


# ============================================================================
# MODELO: SOLICITUD DE CARTA DE PRESENTACIÓN
# ============================================================================

class PresentationLetterRequest(models.Model):
    """
    Solicitud de Carta de Presentación.
    
    Primer paso del proceso de prácticas: el estudiante solicita una carta
    de presentación oficial de la universidad para presentar ante la empresa.
    
    Flujo:
    1. PRACTICANTE crea solicitud (DRAFT)
    2. PRACTICANTE envía a revisión (PENDING)
    3. SECRETARIA valida y aprueba (APPROVED)
    4. SECRETARIA genera PDF de carta (GENERATED)
    5. PRACTICANTE descarga carta
    """
    
    STATUS_CHOICES = [
        ('DRAFT', 'Borrador'),
        ('PENDING', 'Pendiente de revisión'),
        ('APPROVED', 'Aprobado'),
        ('REJECTED', 'Rechazado'),
        ('GENERATED', 'Carta generada'),
        ('USED', 'Usada en práctica'),
    ]
    
    # Primary Key
    id = models.AutoField(primary_key=True)
    
    # ========================================================================
    # RELACIONES
    # ========================================================================
    
    student = models.ForeignKey(
        'StudentProfile',
        on_delete=models.CASCADE,
        related_name='presentation_letter_requests',
        verbose_name='Estudiante',
        help_text='Estudiante que solicita la carta'
    )
    
    assigned_secretary = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'rol_id__nombre': 'SECRETARIA'},
        related_name='assigned_letter_requests',
        verbose_name='Secretaria Asignada',
        db_column='assigned_secretary_id'
    )
    
    # NUEVO: Relación con Escuela Profesional
    escuela = models.ForeignKey(
        'School',
        on_delete=models.PROTECT,
        related_name='presentation_letters',
        verbose_name='Escuela Profesional',
        help_text='Escuela profesional del estudiante',
        null=True,
        blank=True,
        db_column='escuela_id'
    )
    
    # NUEVO: Relación con Empresa
    empresa = models.ForeignKey(
        'Company',
        on_delete=models.PROTECT,
        related_name='presentation_letters',
        verbose_name='Empresa',
        help_text='Empresa donde realizará la práctica (opcional)',
        null=True,
        blank=True,
        db_column='empresa_id'
    )
    
    # ========================================================================
    # DATOS DEL ESTUDIANTE (desnormalizados para el PDF)
    # ========================================================================
    
    ep = models.CharField(
        'E.P. (Escuela Profesional)',
        max_length=200,
        help_text='Auto-rellenado desde escuela.nombre',
        blank=True
    )
    
    student_full_name = models.CharField(
        'Nombre Completo del Alumno',
        max_length=200
    )
    
    student_code = models.CharField(
        'Código del Estudiante',
        max_length=20
    )
    
    year_of_study = models.CharField(
        'Año de Estudios',
        max_length=50,
        help_text='Ejemplo: Quinto año'
    )
    
    study_cycle = models.CharField(
        'Ciclo de Estudios',
        max_length=10,
        help_text='Ejemplo: IX'
    )
    
    student_email = models.EmailField(
        'Email del Estudiante',
        max_length=100
    )
    
    # ========================================================================
    # DATOS DE LA EMPRESA
    # ========================================================================
    
    company_name = models.CharField(
        'Nombre de la Empresa',
        max_length=255,
        help_text='Auto-rellenado desde empresa.nombre si se selecciona empresa',
        blank=True
    )
    
    company_representative = models.CharField(
        'Nombre del Representante',
        max_length=200,
        help_text='Persona de contacto específica para esta solicitud'
    )
    
    company_position = models.CharField(
        'Cargo del Representante / Grado Académico',
        max_length=100,
        help_text='Ejemplo: Gerente de Recursos Humanos'
    )
    
    company_phone = models.CharField(
        'Teléfono - Fax',
        max_length=50,
        help_text='Teléfono de contacto (puede ser diferente al de la empresa)'
    )
    
    company_address = models.TextField(
        'Dirección de la Empresa',
        help_text='Auto-rellenado desde empresa.direccion si se selecciona empresa',
        blank=True
    )
    
    practice_area = models.CharField(
        'Área de Práctica',
        max_length=100,
        help_text='Ejemplo: Desarrollo de Software, Redes, Base de Datos'
    )
    
    # ========================================================================
    # FECHAS
    # ========================================================================
    
    start_date = models.DateField(
        'Fecha de Inicio',
        help_text='Fecha aproximada de inicio de práctica'
    )
    
    # ========================================================================
    # ESTADO Y RESULTADO
    # ========================================================================
    
    status = models.CharField(
        'Estado',
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    
    letter_document = models.ForeignKey(
        'Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presentation_letter',
        verbose_name='Documento de Carta Generada',
        help_text='PDF de la carta de presentación generada'
    )
    
    rejection_reason = models.TextField(
        'Motivo de Rechazo',
        blank=True,
        null=True,
        help_text='Razón por la cual la secretaria rechazó la solicitud'
    )
    
    # ========================================================================
    # METADATA Y TIMESTAMPS
    # ========================================================================
    
    created_at = models.DateTimeField(
        'Fecha de Creación',
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        'Última Actualización',
        auto_now=True
    )
    
    submitted_at = models.DateTimeField(
        'Fecha de Envío',
        null=True,
        blank=True,
        help_text='Cuando se envió a secretaría'
    )
    
    reviewed_at = models.DateTimeField(
        'Fecha de Revisión',
        null=True,
        blank=True,
        help_text='Cuando la secretaria revisó'
    )
    
    class Meta:
        db_table = 'presentation_letter_requests'
        verbose_name = 'Solicitud de Carta de Presentación'
        verbose_name_plural = 'Solicitudes de Carta de Presentación'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['assigned_secretary', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['student_code']),
        ]
    
    def __str__(self):
        return f"Carta {self.student_code} - {self.company_name} ({self.get_status_display()})"
    
    def can_edit(self):
        """Permite edición solo en estado DRAFT o REJECTED."""
        return self.status in ['DRAFT', 'REJECTED']
    
    def can_submit(self):
        """Permite envío solo desde DRAFT."""
        return self.status == 'DRAFT'
    
    def can_approve(self):
        """Permite aprobación solo desde PENDING."""
        return self.status == 'PENDING'
    
    def can_generate_pdf(self):
        """Permite generar PDF solo si está APPROVED y no tiene documento."""
        return self.status == 'APPROVED' and not self.letter_document
    
    def save(self, *args, **kwargs):
        """Auto-rellenar datos del estudiante al crear."""
        # Verificar si tiene student_id en lugar de acceder directamente a student
        if not self.pk and self.student_id:  # Solo al crear y si hay student_id
            try:
                self.student_full_name = f"{self.student.usuario.nombres} {self.student.usuario.apellidos}"
                self.student_code = self.student.codigo
                self.student_email = self.student.usuario.correo
                
                # Auto-asignar escuela desde el perfil del estudiante
                if self.student.escuela and not self.escuela_id:
                    self.escuela = self.student.escuela
                
                # Auto-rellenar nombre de escuela
                if self.escuela:
                    self.ep = self.escuela.nombre
            except (AttributeError, self.student.RelatedObjectDoesNotExist):
                # Si hay algún problema accediendo a los datos del estudiante, continuar
                pass
        
        # Auto-rellenar datos de la empresa si se seleccionó una
        if self.empresa_id:
            try:
                if not self.company_name:
                    self.company_name = self.empresa.nombre
                if not self.company_address:
                    self.company_address = self.empresa.direccion or ''
            except (AttributeError, self.empresa.RelatedObjectDoesNotExist):
                pass
        
        super().save(*args, **kwargs)

