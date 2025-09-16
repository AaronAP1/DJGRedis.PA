"""
Modelos de Django para el sistema de gestión de prácticas profesionales.
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from uuid import uuid4
import os


class CustomUserManager(BaseUserManager):
    """Manager personalizado para el modelo User."""

    def create_user(self, email, password=None, **extra_fields):
        """Crea y guarda un usuario regular."""
        if not email:
            raise ValueError('El email es obligatorio')
        
        email = self.normalize_email(email)
        # Generar/normalizar username si no se proporcionó
        username = extra_fields.get('username')
        if not username:
            try:
                username = email.split('@')[0]
            except Exception:
                username = email
        base = username.strip().lower().replace(' ', '.')
        candidate = base
        i = 0
        # Asegurar unicidad
        while self.model.objects.filter(username__iexact=candidate).exists():
            i += 1
            candidate = f"{base}{i}"
        extra_fields['username'] = candidate

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Crea y guarda un superusuario."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMINISTRADOR')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Modelo de Usuario personalizado."""
    
    ROLE_CHOICES = [
        ('PRACTICANTE', 'Practicante'),
        ('SUPERVISOR', 'Supervisor'),
        ('COORDINADOR', 'Coordinador'),
        ('SECRETARIA', 'Secretaria'),
        ('ADMINISTRADOR', 'Administrador'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    email = models.EmailField('Email', unique=True)
    username = models.CharField('Usuario', max_length=150, unique=True, blank=True, null=True)
    first_name = models.CharField('Nombres', max_length=150)
    last_name = models.CharField('Apellidos', max_length=150)
    role = models.CharField('Rol', max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField('Activo', default=True)
    is_staff = models.BooleanField('Es staff', default=False)
    date_joined = models.DateTimeField('Fecha de registro', auto_now_add=True)
    last_login = models.DateTimeField('Último acceso', null=True, blank=True)
    created_at = models.DateTimeField('Creado en', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado en', auto_now=True)
    photo = models.ImageField('Foto de perfil', upload_to='users/photos/%Y/%m/', blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']

    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]

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
        return self.role == 'PRACTICANTE'

    @property
    def is_supervisor(self):
        return self.role == 'SUPERVISOR'

    @property
    def is_coordinador(self):
        return self.role == 'COORDINADOR'

    @property
    def is_secretaria(self):
        return self.role == 'SECRETARIA'

    @property
    def is_administrador(self):
        return self.role == 'ADMINISTRADOR'


class Student(models.Model):
    """Modelo de Estudiante."""
    
    DOCUMENTO_CHOICES = [
        ('DNI', 'DNI'),
        ('CE', 'Carnet de Extranjería'),
        ('PASSPORT', 'Pasaporte'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    codigo_estudiante = models.CharField(
        'Código de estudiante', 
        max_length=10, 
        unique=True,
        validators=[RegexValidator(r'^20\d{8}$', 'Formato inválido. Ej: 2021001234')]
    )
    documento_tipo = models.CharField('Tipo de documento', max_length=10, choices=DOCUMENTO_CHOICES, blank=True, null=True)
    documento_numero = models.CharField('Número de documento', max_length=20, blank=True, null=True)
    telefono = models.CharField('Teléfono', max_length=15, blank=True, null=True)
    direccion = models.TextField('Dirección', blank=True, null=True)
    carrera = models.CharField('Carrera', max_length=100, blank=True, null=True)
    semestre_actual = models.PositiveIntegerField(
        'Semestre actual', 
        blank=True, 
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    promedio_ponderado = models.DecimalField(
        'Promedio ponderado', 
        max_digits=4, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    created_at = models.DateTimeField('Creado en', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado en', auto_now=True)

    class Meta:
        db_table = 'students'
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'
        unique_together = [['documento_tipo', 'documento_numero']]
        indexes = [
            models.Index(fields=['codigo_estudiante']),
            models.Index(fields=['documento_numero']),
            models.Index(fields=['carrera']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.codigo_estudiante}"

    @property
    def puede_realizar_practica(self):
        """Verifica si el estudiante puede realizar práctica."""
        return (
            self.semestre_actual and self.semestre_actual >= 6 and
            self.promedio_ponderado and self.promedio_ponderado >= 12.0
        )

    @property
    def año_ingreso(self):
        """Extrae el año de ingreso del código de estudiante."""
        return int(self.codigo_estudiante[:4])


class Company(models.Model):
    """Modelo de Empresa."""
    
    STATUS_CHOICES = [
        ('PENDING_VALIDATION', 'Pendiente de validación'),
        ('ACTIVE', 'Activa'),
        ('INACTIVE', 'Inactiva'),
        ('SUSPENDED', 'Suspendida'),
        ('BLACKLISTED', 'Lista negra'),
    ]

    TAMAÑO_CHOICES = [
        ('MICRO', 'Microempresa'),
        ('PEQUEÑA', 'Pequeña empresa'),
        ('MEDIANA', 'Mediana empresa'),
        ('GRANDE', 'Gran empresa'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    ruc = models.CharField(
        'RUC', 
        max_length=11, 
        unique=True,
        validators=[RegexValidator(r'^\d{11}$', 'RUC debe tener 11 dígitos')]
    )
    razon_social = models.CharField('Razón social', max_length=200)
    nombre_comercial = models.CharField('Nombre comercial', max_length=200, blank=True, null=True)
    direccion = models.TextField('Dirección', blank=True, null=True)
    telefono = models.CharField('Teléfono', max_length=15, blank=True, null=True)
    email = models.EmailField('Email', blank=True, null=True)
    sector_economico = models.CharField('Sector económico', max_length=100, blank=True, null=True)
    tamaño_empresa = models.CharField('Tamaño', max_length=20, choices=TAMAÑO_CHOICES, blank=True, null=True)
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='PENDING_VALIDATION')
    fecha_validacion = models.DateTimeField('Fecha de validación', blank=True, null=True)
    created_at = models.DateTimeField('Creado en', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado en', auto_now=True)

    class Meta:
        db_table = 'companies'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        indexes = [
            models.Index(fields=['ruc']),
            models.Index(fields=['status']),
            models.Index(fields=['sector_economico']),
        ]

    def __str__(self):
        return self.nombre_comercial or self.razon_social

    @property
    def nombre_para_mostrar(self):
        """Retorna el nombre comercial o razón social."""
        return self.nombre_comercial or self.razon_social

    @property
    def puede_recibir_practicantes(self):
        """Verifica si la empresa puede recibir practicantes."""
        return self.status == 'ACTIVE'


class Supervisor(models.Model):
    """Modelo de Supervisor de empresa."""
    
    DOCUMENTO_CHOICES = [
        ('DNI', 'DNI'),
        ('CE', 'Carnet de Extranjería'),
        ('PASSPORT', 'Pasaporte'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='supervisor_profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='supervisors')
    documento_tipo = models.CharField('Tipo de documento', max_length=10, choices=DOCUMENTO_CHOICES)
    documento_numero = models.CharField('Número de documento', max_length=20)
    cargo = models.CharField('Cargo', max_length=100)
    telefono = models.CharField('Teléfono', max_length=15, blank=True, null=True)
    años_experiencia = models.PositiveIntegerField('Años de experiencia', blank=True, null=True)
    created_at = models.DateTimeField('Creado en', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado en', auto_now=True)

    class Meta:
        db_table = 'supervisors'
        verbose_name = 'Supervisor'
        verbose_name_plural = 'Supervisores'
        unique_together = [['documento_tipo', 'documento_numero']]
        indexes = [
            models.Index(fields=['documento_numero']),
            models.Index(fields=['company']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.company.nombre_para_mostrar}"


class Practice(models.Model):
    """Modelo de Práctica Profesional."""
    
    STATUS_CHOICES = [
        ('DRAFT', 'Borrador'),
        ('PENDING', 'Pendiente'),
        ('APPROVED', 'Aprobada'),
        ('IN_PROGRESS', 'En progreso'),
        ('COMPLETED', 'Completada'),
        ('CANCELLED', 'Cancelada'),
        ('SUSPENDED', 'Suspendida'),
    ]

    MODALIDAD_CHOICES = [
        ('PRESENCIAL', 'Presencial'),
        ('REMOTO', 'Remoto'),
        ('HIBRIDO', 'Híbrido'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='practices')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='practices')
    supervisor = models.ForeignKey(Supervisor, on_delete=models.SET_NULL, null=True, blank=True, related_name='practices')
    titulo = models.CharField('Título', max_length=200)
    descripcion = models.TextField('Descripción')
    objetivos = models.JSONField('Objetivos', default=list)
    fecha_inicio = models.DateTimeField('Fecha de inicio', blank=True, null=True)
    fecha_fin = models.DateTimeField('Fecha de fin', blank=True, null=True)
    horas_totales = models.PositiveIntegerField('Horas totales', default=0)
    modalidad = models.CharField('Modalidad', max_length=20, choices=MODALIDAD_CHOICES, default='PRESENCIAL')
    area_practica = models.CharField('Área de práctica', max_length=100, blank=True, null=True)
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    calificacion_final = models.DecimalField(
        'Calificación final', 
        max_digits=4, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    observaciones = models.TextField('Observaciones', blank=True)
    created_at = models.DateTimeField('Creado en', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado en', auto_now=True)

    class Meta:
        db_table = 'practices'
        verbose_name = 'Práctica'
        verbose_name_plural = 'Prácticas'
        indexes = [
            models.Index(fields=['student']),
            models.Index(fields=['company']),
            models.Index(fields=['supervisor']),
            models.Index(fields=['status']),
            models.Index(fields=['fecha_inicio']),
            models.Index(fields=['fecha_fin']),
        ]

    def __str__(self):
        return f"{self.titulo} - {self.student.user.get_full_name()}"

    @property
    def duracion_dias(self):
        """Retorna la duración en días."""
        if self.fecha_inicio and self.fecha_fin:
            return (self.fecha_fin - self.fecha_inicio).days
        return 0

    @property
    def esta_activa(self):
        """Verifica si la práctica está activa."""
        return self.status == 'IN_PROGRESS'


class Document(models.Model):
    """Modelo de Documento."""
    
    TIPO_CHOICES = [
        ('PRACTICE_AGREEMENT', 'Convenio de práctica'),
        ('EVALUATION_REPORT', 'Reporte de evaluación'),
        ('FINAL_REPORT', 'Reporte final'),
        ('COMPANY_VALIDATION', 'Validación de empresa'),
        ('STUDENT_CV', 'CV del estudiante'),
        ('ACADEMIC_RECORD', 'Récord académico'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    practice = models.ForeignKey(Practice, on_delete=models.CASCADE, related_name='documents')
    tipo = models.CharField('Tipo', max_length=30, choices=TIPO_CHOICES)
    nombre_archivo = models.CharField('Nombre del archivo', max_length=255)
    archivo = models.FileField('Archivo', upload_to='documents/%Y/%m/')
    tamaño_bytes = models.PositiveIntegerField('Tamaño en bytes')
    mime_type = models.CharField('Tipo MIME', max_length=100)
    subido_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_documents')
    aprobado = models.BooleanField('Aprobado', default=False)
    fecha_aprobacion = models.DateTimeField('Fecha de aprobación', blank=True, null=True)
    aprobado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_documents')
    created_at = models.DateTimeField('Creado en', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado en', auto_now=True)

    class Meta:
        db_table = 'documents'
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        indexes = [
            models.Index(fields=['practice']),
            models.Index(fields=['tipo']),
            models.Index(fields=['aprobado']),
        ]

    def __str__(self):
        return f"{self.nombre_archivo} - {self.practice.titulo}"

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
    """Modelo de Notificación."""
    
    TIPO_CHOICES = [
        ('INFO', 'Información'),
        ('SUCCESS', 'Éxito'),
        ('WARNING', 'Advertencia'),
        ('ERROR', 'Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    titulo = models.CharField('Título', max_length=200)
    mensaje = models.TextField('Mensaje')
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES, default='INFO')
    leida = models.BooleanField('Leída', default=False)
    fecha_lectura = models.DateTimeField('Fecha de lectura', blank=True, null=True)
    accion_url = models.URLField('URL de acción', blank=True, null=True)
    created_at = models.DateTimeField('Creado en', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado en', auto_now=True)

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'leida']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.titulo} - {self.user.get_full_name()}"

    @property
    def es_importante(self):
        """Verifica si la notificación es importante."""
        return self.tipo in ['WARNING', 'ERROR']
