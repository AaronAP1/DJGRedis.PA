"""
Serializers completos para todas las entidades del sistema.

Este módulo contiene serializers REST para:
- Users (Usuarios del sistema)
- Students (Estudiantes/Practicantes)
- Companies (Empresas)
- Supervisors (Supervisores de empresas)
- Practices (Prácticas profesionales)
- Documents (Documentos)
- Notifications (Notificaciones)

Cada entidad incluye:
- ListSerializer: Vista resumida para listados
- DetailSerializer: Vista completa con relaciones
- CreateSerializer: Creación con validaciones
- UpdateSerializer: Actualización parcial
- Serializers adicionales para acciones específicas (aprobar, cambiar estado, etc.)

Incluye validaciones personalizadas y campos computados basados en roles.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from src.adapters.secondary.database.models import (
    Student, Company, Supervisor, Practice, Document, Notification, Avatar,
    Role, Permission, RolePermission, UserPermission
)
from datetime import datetime, timedelta
import os

User = get_user_model()


# ============================================================================
# SERIALIZERS DE SEGURIDAD (RBAC)
# ============================================================================

class PermissionSerializer(serializers.ModelSerializer):
    """Serializer para permisos del sistema."""
    
    class Meta:
        model = Permission
        fields = ['id', 'code', 'name', 'description', 'module', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class PermissionListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listar permisos."""
    
    class Meta:
        model = Permission
        fields = ['id', 'code', 'name', 'module', 'is_active']


class RolePermissionSerializer(serializers.ModelSerializer):
    """Serializer para la relación Role-Permission."""
    
    permission = PermissionSerializer(read_only=True)
    permission_id = serializers.UUIDField(write_only=True)
    granted_by_email = serializers.EmailField(source='granted_by.email', read_only=True)
    
    class Meta:
        model = RolePermission
        fields = ['id', 'permission', 'permission_id', 'granted_by', 'granted_by_email', 'granted_at']
        read_only_fields = ['id', 'granted_by', 'granted_at']


class RoleSerializer(serializers.ModelSerializer):
    """Serializer completo para roles con permisos."""
    
    permissions = PermissionListSerializer(many=True, read_only=True)
    permissions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = [
            'id', 'code', 'name', 'description', 
            'permissions', 'permissions_count',
            'is_active', 'is_system', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_permissions_count(self, obj):
        """Retorna cantidad de permisos activos del rol."""
        return obj.permissions.filter(is_active=True).count()


class RoleListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listar roles."""
    
    permissions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = ['id', 'code', 'name', 'permissions_count', 'is_active', 'is_system']
    
    def get_permissions_count(self, obj):
        return obj.permissions.filter(is_active=True).count()


class RoleCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear roles."""
    
    permission_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="Lista de IDs de permisos a asignar al rol"
    )
    
    class Meta:
        model = Role
        fields = ['code', 'name', 'description', 'is_active', 'permission_ids']
    
    def validate_code(self, value):
        """Validar que el código sea único y en mayúsculas."""
        value = value.upper()
        if Role.objects.filter(code=value).exists():
            raise serializers.ValidationError('Ya existe un rol con este código')
        return value
    
    def create(self, validated_data):
        """Crear rol y asignar permisos."""
        permission_ids = validated_data.pop('permission_ids', [])
        role = Role.objects.create(**validated_data)
        
        # Asignar permisos si se proporcionaron
        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids, is_active=True)
            role.permissions.set(permissions)
        
        return role


class UserPermissionSerializer(serializers.ModelSerializer):
    """Serializer para permisos específicos de usuario (overrides)."""
    
    permission = PermissionSerializer(read_only=True)
    permission_id = serializers.UUIDField(write_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    granted_by_email = serializers.EmailField(source='granted_by.email', read_only=True)
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = UserPermission
        fields = [
            'id', 'user', 'user_email', 'permission', 'permission_id',
            'permission_type', 'granted_by', 'granted_by_email',
            'reason', 'granted_at', 'expires_at', 'is_expired'
        ]
        read_only_fields = ['id', 'granted_by', 'granted_at']
    
    def get_is_expired(self, obj):
        """Verifica si el permiso ha expirado."""
        if obj.expires_at is None:
            return False
        from django.utils import timezone
        return timezone.now() > obj.expires_at


class UserPermissionCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear/otorgar permisos a usuarios."""
    
    class Meta:
        model = UserPermission
        fields = ['user', 'permission', 'permission_type', 'reason', 'expires_at']
    
    def validate(self, attrs):
        """Validar que no exista ya un permiso igual para el usuario."""
        user = attrs.get('user')
        permission = attrs.get('permission')
        
        # Verificar si ya existe
        existing = UserPermission.objects.filter(
            user=user,
            permission=permission
        ).first()
        
        if existing:
            raise serializers.ValidationError(
                f'El usuario ya tiene un override para el permiso "{permission.code}"'
            )
        
        return attrs


# ============================================================================
# SERIALIZERS DE AVATAR
# ============================================================================

class AvatarSerializer(serializers.ModelSerializer):
    """Serializer para mostrar avatares disponibles."""
    
    class Meta:
        model = Avatar
        fields = ['id', 'url', 'role', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


# ============================================================================
# SERIALIZERS DE USUARIOS (USER)
# ============================================================================

class UserListSerializer(serializers.ModelSerializer):
    """Serializer simple para listar usuarios (sin datos sensibles)."""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'role', 'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para ver/actualizar usuarios."""
    
    avatar = AvatarSerializer(read_only=True)
    avatar_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    full_name = serializers.SerializerMethodField()
    short_name = serializers.SerializerMethodField()
    is_practicante = serializers.BooleanField(read_only=True)
    is_supervisor = serializers.BooleanField(read_only=True)
    is_coordinador = serializers.BooleanField(read_only=True)
    is_secretaria = serializers.BooleanField(read_only=True)
    is_administrador = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'short_name', 'role', 'is_active', 'is_staff',
            'date_joined', 'last_login', 'created_at', 'updated_at',
            'avatar', 'avatar_id', 'is_practicante', 'is_supervisor', 
            'is_coordinador', 'is_secretaria', 'is_administrador'
        ]
        read_only_fields = [
            'id', 'date_joined', 'last_login', 'created_at', 'updated_at',
            'is_practicante', 'is_supervisor', 'is_coordinador',
            'is_secretaria', 'is_administrador'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_short_name(self, obj):
        return obj.get_short_name()
    
    def validate_email(self, value):
        """Validar que el email sea único y tenga dominio válido."""
        # Verificar unicidad
        user_id = self.instance.id if self.instance else None
        if User.objects.filter(email=value).exclude(id=user_id).exists():
            raise serializers.ValidationError('Este email ya está registrado')
        
        # Validar dominio (solo @upeu.edu.pe para practicantes)
        if self.initial_data.get('role') == 'PRACTICANTE':
            if not value.endswith('@upeu.edu.pe'):
                raise serializers.ValidationError(
                    'Los practicantes deben usar correo institucional (@upeu.edu.pe)'
                )
        
        return value
    
    def validate_role(self, value):
        """Validar que el rol sea válido."""
        valid_roles = ['PRACTICANTE', 'SUPERVISOR', 'COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']
        if value not in valid_roles:
            raise serializers.ValidationError(f'Rol inválido. Opciones: {", ".join(valid_roles)}')
        return value


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear nuevos usuarios."""
    
    avatar = AvatarSerializer(read_only=True)
    avatar_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name',
            'role', 'password', 'password_confirm', 'avatar', 'avatar_id'
        ]
    
    def validate(self, attrs):
        """Validar que las contraseñas coincidan."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden'
            })
        return attrs
    
    def validate_email(self, value):
        """Validar email único y dominio."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este email ya está registrado')
        
        # Validar dominio para practicantes
        role = self.initial_data.get('role')
        if role == 'PRACTICANTE' and not value.endswith('@upeu.edu.pe'):
            raise serializers.ValidationError(
                'Los practicantes deben usar correo institucional (@upeu.edu.pe)'
            )
        
        return value
    
    def create(self, validated_data):
        """Crear usuario con contraseña hasheada."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar usuarios (sin cambiar contraseña)."""
    
    avatar = AvatarSerializer(read_only=True)
    avatar_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'is_active', 'avatar', 'avatar_id'
        ]
    
    def validate(self, attrs):
        """Solo staff puede desactivar usuarios."""
        request = self.context.get('request')
        if 'is_active' in attrs and request:
            user = request.user
            if user.role not in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']:
                attrs.pop('is_active', None)
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para cambiar contraseña."""
    
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validar contraseñas."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Las contraseñas no coinciden'
            })
        return attrs
    
    def validate_old_password(self, value):
        """Validar contraseña actual."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Contraseña actual incorrecta')
        return value


# ============================================================================
# SERIALIZERS DE ESTUDIANTES (STUDENT)
# ============================================================================

class StudentListSerializer(serializers.ModelSerializer):
    """Serializer simple para listar estudiantes."""
    
    user = UserListSerializer(read_only=True)
    puede_realizar_practica = serializers.BooleanField(read_only=True)
    año_ingreso = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Student
        fields = [
            'id', 'user', 'codigo_estudiante', 'carrera', 'semestre_actual',
            'promedio_ponderado', 'puede_realizar_practica', 'año_ingreso',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudentDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para estudiantes."""
    
    user = UserDetailSerializer(read_only=True)
    puede_realizar_practica = serializers.BooleanField(read_only=True)
    año_ingreso = serializers.IntegerField(read_only=True)
    total_practices = serializers.SerializerMethodField()
    completed_practices = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'user', 'codigo_estudiante', 'documento_tipo', 'documento_numero',
            'telefono', 'direccion', 'carrera', 'semestre_actual', 'promedio_ponderado',
            'puede_realizar_practica', 'año_ingreso', 'total_practices',
            'completed_practices', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_practices(self, obj):
        """Total de prácticas del estudiante."""
        return obj.practices.count()
    
    def get_completed_practices(self, obj):
        """Prácticas completadas."""
        return obj.practices.filter(status='COMPLETED').count()


class StudentCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear estudiantes."""
    
    # Datos del usuario
    email = serializers.EmailField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = Student
        fields = [
            'email', 'first_name', 'last_name', 'password',
            'codigo_estudiante', 'documento_tipo', 'documento_numero',
            'telefono', 'direccion', 'carrera', 'semestre_actual', 'promedio_ponderado'
        ]
    
    def validate_email(self, value):
        """Validar email institucional."""
        if not value.endswith('@upeu.edu.pe'):
            raise serializers.ValidationError(
                'Debe usar correo institucional (@upeu.edu.pe)'
            )
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este email ya está registrado')
        return value
    
    def validate_codigo_estudiante(self, value):
        """Validar formato de código de estudiante."""
        import re
        if not re.match(r'^20\d{8}$', value):
            raise serializers.ValidationError(
                'Formato inválido. Debe ser: 20XXXXXXXX (10 dígitos)'
            )
        if Student.objects.filter(codigo_estudiante=value).exists():
            raise serializers.ValidationError('Este código ya está registrado')
        return value
    
    def validate_promedio_ponderado(self, value):
        """Validar rango de promedio."""
        if value and (value < 0 or value > 20):
            raise serializers.ValidationError('El promedio debe estar entre 0 y 20')
        return value
    
    def validate_semestre_actual(self, value):
        """Validar rango de semestre."""
        if value and (value < 1 or value > 12):
            raise serializers.ValidationError('El semestre debe estar entre 1 y 12')
        return value
    
    def validate(self, attrs):
        """Validaciones cruzadas."""
        # Verificar que puede hacer prácticas
        semestre = attrs.get('semestre_actual')
        promedio = attrs.get('promedio_ponderado')
        
        if semestre and semestre < 6:
            raise serializers.ValidationError({
                'semestre_actual': 'Debe estar en 6to semestre o superior para realizar prácticas'
            })
        
        if promedio and promedio < 12.0:
            raise serializers.ValidationError({
                'promedio_ponderado': 'El promedio mínimo para prácticas es 12.0'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Crear usuario y estudiante."""
        # Extraer datos del usuario
        email = validated_data.pop('email')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        password = validated_data.pop('password')
        
        # Crear usuario
        user = User.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            role='PRACTICANTE'
        )
        
        # Crear estudiante
        student = Student.objects.create(user=user, **validated_data)
        return student


class StudentUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar estudiantes."""
    
    class Meta:
        model = Student
        fields = [
            'documento_tipo', 'documento_numero', 'telefono', 'direccion',
            'carrera', 'semestre_actual', 'promedio_ponderado'
        ]
    
    def validate_promedio_ponderado(self, value):
        """Validar rango de promedio."""
        if value and (value < 0 or value > 20):
            raise serializers.ValidationError('El promedio debe estar entre 0 y 20')
        return value
    
    def validate_semestre_actual(self, value):
        """Validar rango de semestre."""
        if value and (value < 1 or value > 12):
            raise serializers.ValidationError('El semestre debe estar entre 1 y 12')
        return value


# ============================================================================
# SERIALIZERS DE EMPRESAS (COMPANY)
# ============================================================================

class CompanyListSerializer(serializers.ModelSerializer):
    """Serializer simple para listar empresas."""
    
    nombre_para_mostrar = serializers.CharField(read_only=True)
    puede_recibir_practicantes = serializers.BooleanField(read_only=True)
    total_supervisors = serializers.SerializerMethodField()
    total_practices = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = [
            'id', 'ruc', 'razon_social', 'nombre_comercial', 'nombre_para_mostrar',
            'sector_economico', 'tamaño_empresa', 'status', 'puede_recibir_practicantes',
            'total_supervisors', 'total_practices', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_supervisors(self, obj):
        """Total de supervisores."""
        return obj.supervisors.count()
    
    def get_total_practices(self, obj):
        """Total de prácticas."""
        return obj.practices.count()


class CompanyDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para empresas."""
    
    nombre_para_mostrar = serializers.CharField(read_only=True)
    puede_recibir_practicantes = serializers.BooleanField(read_only=True)
    total_supervisors = serializers.SerializerMethodField()
    total_practices = serializers.SerializerMethodField()
    active_practices = serializers.SerializerMethodField()
    completed_practices = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = [
            'id', 'ruc', 'razon_social', 'nombre_comercial', 'nombre_para_mostrar',
            'direccion', 'telefono', 'email', 'sector_economico', 'tamaño_empresa',
            'status', 'fecha_validacion', 'puede_recibir_practicantes',
            'total_supervisors', 'total_practices', 'active_practices',
            'completed_practices', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'fecha_validacion', 'created_at', 'updated_at']
    
    def get_total_supervisors(self, obj):
        return obj.supervisors.count()
    
    def get_total_practices(self, obj):
        return obj.practices.count()
    
    def get_active_practices(self, obj):
        return obj.practices.filter(status='IN_PROGRESS').count()
    
    def get_completed_practices(self, obj):
        return obj.practices.filter(status='COMPLETED').count()


class CompanyCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear empresas."""
    
    class Meta:
        model = Company
        fields = [
            'ruc', 'razon_social', 'nombre_comercial', 'direccion',
            'telefono', 'email', 'sector_economico', 'tamaño_empresa'
        ]
    
    def validate_ruc(self, value):
        """Validar RUC de 11 dígitos."""
        import re
        if not re.match(r'^\d{11}$', value):
            raise serializers.ValidationError('El RUC debe tener 11 dígitos')
        if Company.objects.filter(ruc=value).exists():
            raise serializers.ValidationError('Este RUC ya está registrado')
        return value
    
    def validate_email(self, value):
        """Validar email único."""
        if value and Company.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este email ya está registrado')
        return value
    
    def create(self, validated_data):
        """Crear empresa con estado PENDING_VALIDATION."""
        validated_data['status'] = 'PENDING_VALIDATION'
        return super().create(validated_data)


class CompanyUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar empresas."""
    
    class Meta:
        model = Company
        fields = [
            'razon_social', 'nombre_comercial', 'direccion',
            'telefono', 'email', 'sector_economico', 'tamaño_empresa'
        ]
    
    def validate_email(self, value):
        """Validar email único."""
        company_id = self.instance.id if self.instance else None
        if value and Company.objects.filter(email=value).exclude(id=company_id).exists():
            raise serializers.ValidationError('Este email ya está registrado')
        return value


class CompanyValidateSerializer(serializers.Serializer):
    """Serializer para validar empresas."""
    
    status = serializers.ChoiceField(
        choices=['ACTIVE', 'SUSPENDED', 'BLACKLISTED'],
        required=True
    )
    observaciones = serializers.CharField(required=False, allow_blank=True)
    
    def validate_status(self, value):
        """Solo puede validarse a ACTIVE."""
        if value not in ['ACTIVE', 'SUSPENDED', 'BLACKLISTED']:
            raise serializers.ValidationError('Estado inválido para validación')
        return value


# ============================================================================
# SERIALIZERS DE SUPERVISORES (SUPERVISOR)
# ============================================================================

class SupervisorListSerializer(serializers.ModelSerializer):
    """Serializer simple para listar supervisores."""
    
    user = UserListSerializer(read_only=True)
    company = CompanyListSerializer(read_only=True)
    total_practices = serializers.SerializerMethodField()
    
    class Meta:
        model = Supervisor
        fields = [
            'id', 'user', 'company', 'documento_tipo', 'documento_numero',
            'cargo', 'telefono', 'años_experiencia', 'total_practices',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_practices(self, obj):
        """Total de prácticas supervisadas."""
        return obj.practices.count()


class SupervisorDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para supervisores."""
    
    user = UserDetailSerializer(read_only=True)
    company = CompanyListSerializer(read_only=True)
    total_practices = serializers.SerializerMethodField()
    active_practices = serializers.SerializerMethodField()
    completed_practices = serializers.SerializerMethodField()
    
    class Meta:
        model = Supervisor
        fields = [
            'id', 'user', 'company', 'documento_tipo', 'documento_numero',
            'cargo', 'telefono', 'años_experiencia', 'total_practices',
            'active_practices', 'completed_practices', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_practices(self, obj):
        return obj.practices.count()
    
    def get_active_practices(self, obj):
        return obj.practices.filter(status='IN_PROGRESS').count()
    
    def get_completed_practices(self, obj):
        return obj.practices.filter(status='COMPLETED').count()


class SupervisorCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear supervisores."""
    
    # Datos del usuario
    email = serializers.EmailField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    company_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Supervisor
        fields = [
            'email', 'first_name', 'last_name', 'password', 'company_id',
            'documento_tipo', 'documento_numero', 'cargo', 'telefono', 'años_experiencia'
        ]
    
    def validate_email(self, value):
        """Validar email único."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este email ya está registrado')
        return value
    
    def validate_company_id(self, value):
        """Validar que la empresa exista y esté activa."""
        try:
            company = Company.objects.get(id=value)
            if company.status not in ['ACTIVE', 'PENDING_VALIDATION']:
                raise serializers.ValidationError('La empresa no puede recibir supervisores')
        except Company.DoesNotExist:
            raise serializers.ValidationError('Empresa no encontrada')
        return value
    
    def validate_años_experiencia(self, value):
        """Validar años de experiencia."""
        if value and value < 0:
            raise serializers.ValidationError('Los años de experiencia no pueden ser negativos')
        if value and value > 60:
            raise serializers.ValidationError('Los años de experiencia son demasiado altos')
        return value
    
    def create(self, validated_data):
        """Crear usuario y supervisor."""
        # Extraer datos
        email = validated_data.pop('email')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        password = validated_data.pop('password')
        company_id = validated_data.pop('company_id')
        
        # Crear usuario
        user = User.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            role='SUPERVISOR'
        )
        
        # Obtener empresa
        company = Company.objects.get(id=company_id)
        
        # Crear supervisor
        supervisor = Supervisor.objects.create(
            user=user,
            company=company,
            **validated_data
        )
        return supervisor


class SupervisorUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar supervisores."""
    
    class Meta:
        model = Supervisor
        fields = [
            'documento_tipo', 'documento_numero', 'cargo',
            'telefono', 'años_experiencia'
        ]
    
    def validate_años_experiencia(self, value):
        """Validar años de experiencia."""
        if value and value < 0:
            raise serializers.ValidationError('Los años de experiencia no pueden ser negativos')
        if value and value > 60:
            raise serializers.ValidationError('Los años de experiencia son demasiado altos')
        return value


# ============================================================================
# SERIALIZERS DE PRÁCTICAS (PRACTICE)
# ============================================================================

class PracticeListSerializer(serializers.ModelSerializer):
    """Serializer simple para listar prácticas."""
    
    student = StudentListSerializer(read_only=True)
    company = CompanyListSerializer(read_only=True)
    supervisor = SupervisorListSerializer(read_only=True)
    duracion_dias = serializers.IntegerField(read_only=True)
    esta_activa = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Practice
        fields = [
            'id', 'student', 'company', 'supervisor', 'titulo', 'area_practica',
            'fecha_inicio', 'fecha_fin', 'horas_totales', 'modalidad', 'status',
            'duracion_dias', 'esta_activa', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PracticeDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para prácticas."""
    
    student = StudentListSerializer(read_only=True)
    company = CompanyListSerializer(read_only=True)
    supervisor = SupervisorListSerializer(read_only=True)
    duracion_dias = serializers.IntegerField(read_only=True)
    esta_activa = serializers.BooleanField(read_only=True)
    total_documents = serializers.SerializerMethodField()
    approved_documents = serializers.SerializerMethodField()
    progreso_porcentual = serializers.SerializerMethodField()
    
    class Meta:
        model = Practice
        fields = [
            'id', 'student', 'company', 'supervisor', 'titulo', 'descripcion',
            'objetivos', 'fecha_inicio', 'fecha_fin', 'horas_totales', 'modalidad',
            'area_practica', 'status', 'calificacion_final', 'observaciones',
            'duracion_dias', 'esta_activa', 'total_documents', 'approved_documents',
            'progreso_porcentual', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_documents(self, obj):
        """Total de documentos."""
        return obj.documents.count()
    
    def get_approved_documents(self, obj):
        """Documentos aprobados."""
        return obj.documents.filter(aprobado=True).count()
    
    def get_progreso_porcentual(self, obj):
        """Calcular progreso porcentual."""
        if obj.fecha_inicio and obj.fecha_fin:
            ahora = datetime.now().date()
            inicio = obj.fecha_inicio.date() if hasattr(obj.fecha_inicio, 'date') else obj.fecha_inicio
            fin = obj.fecha_fin.date() if hasattr(obj.fecha_fin, 'date') else obj.fecha_fin
            
            if ahora < inicio:
                return 0.0
            if ahora >= fin:
                return 100.0
            
            dias_transcurridos = (ahora - inicio).days
            dias_totales = (fin - inicio).days
            
            if dias_totales == 0:
                return 0.0
            
            return round((dias_transcurridos / dias_totales) * 100, 2)
        return 0.0


class PracticeCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear prácticas."""
    
    student_id = serializers.UUIDField(write_only=True)
    company_id = serializers.UUIDField(write_only=True)
    supervisor_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Practice
        fields = [
            'student_id', 'company_id', 'supervisor_id', 'titulo', 'descripcion',
            'objetivos', 'fecha_inicio', 'fecha_fin', 'horas_totales',
            'modalidad', 'area_practica'
        ]
    
    def validate_student_id(self, value):
        """Validar que el estudiante exista y pueda hacer prácticas."""
        try:
            student = Student.objects.get(id=value)
            if not student.puede_realizar_practica:
                raise serializers.ValidationError(
                    'El estudiante no cumple los requisitos para realizar prácticas '
                    '(semestre >= 6 y promedio >= 12.0)'
                )
        except Student.DoesNotExist:
            raise serializers.ValidationError('Estudiante no encontrado')
        return value
    
    def validate_company_id(self, value):
        """Validar que la empresa exista y esté activa."""
        try:
            company = Company.objects.get(id=value)
            if not company.puede_recibir_practicantes:
                raise serializers.ValidationError('La empresa no puede recibir practicantes')
        except Company.DoesNotExist:
            raise serializers.ValidationError('Empresa no encontrada')
        return value
    
    def validate_supervisor_id(self, value):
        """Validar que el supervisor exista."""
        if value:
            try:
                Supervisor.objects.get(id=value)
            except Supervisor.DoesNotExist:
                raise serializers.ValidationError('Supervisor no encontrado')
        return value
    
    def validate_horas_totales(self, value):
        """Validar horas totales mínimas."""
        if value < 480:
            raise serializers.ValidationError('La práctica debe tener mínimo 480 horas')
        if value > 2000:
            raise serializers.ValidationError('Las horas totales son demasiado altas')
        return value
    
    def validate(self, attrs):
        """Validaciones cruzadas."""
        fecha_inicio = attrs.get('fecha_inicio')
        fecha_fin = attrs.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            if fecha_fin <= fecha_inicio:
                raise serializers.ValidationError({
                    'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio'
                })
            
            # Calcular duración mínima (3 meses)
            duracion = fecha_fin - fecha_inicio
            if duracion.days < 90:
                raise serializers.ValidationError({
                    'fecha_fin': 'La práctica debe durar mínimo 3 meses'
                })
        
        return attrs
    
    def create(self, validated_data):
        """Crear práctica."""
        student_id = validated_data.pop('student_id')
        company_id = validated_data.pop('company_id')
        supervisor_id = validated_data.pop('supervisor_id', None)
        
        student = Student.objects.get(id=student_id)
        company = Company.objects.get(id=company_id)
        supervisor = Supervisor.objects.get(id=supervisor_id) if supervisor_id else None
        
        practice = Practice.objects.create(
            student=student,
            company=company,
            supervisor=supervisor,
            status='DRAFT',
            **validated_data
        )
        return practice


class PracticeUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar prácticas."""
    
    supervisor_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Practice
        fields = [
            'titulo', 'descripcion', 'objetivos', 'fecha_inicio', 'fecha_fin',
            'horas_totales', 'modalidad', 'area_practica', 'supervisor_id', 'observaciones'
        ]
    
    def validate_supervisor_id(self, value):
        """Validar supervisor."""
        if value:
            try:
                Supervisor.objects.get(id=value)
            except Supervisor.DoesNotExist:
                raise serializers.ValidationError('Supervisor no encontrado')
        return value
    
    def validate_horas_totales(self, value):
        """Validar horas totales."""
        if value and value < 480:
            raise serializers.ValidationError('La práctica debe tener mínimo 480 horas')
        return value
    
    def validate(self, attrs):
        """Validar fechas."""
        fecha_inicio = attrs.get('fecha_inicio', self.instance.fecha_inicio)
        fecha_fin = attrs.get('fecha_fin', self.instance.fecha_fin)
        
        if fecha_inicio and fecha_fin:
            if fecha_fin <= fecha_inicio:
                raise serializers.ValidationError({
                    'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio'
                })
        
        return attrs
    
    def update(self, instance, validated_data):
        """Actualizar práctica."""
        supervisor_id = validated_data.pop('supervisor_id', None)
        
        if supervisor_id is not None:
            if supervisor_id:
                instance.supervisor = Supervisor.objects.get(id=supervisor_id)
            else:
                instance.supervisor = None
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class PracticeStatusSerializer(serializers.Serializer):
    """Serializer para cambiar estado de práctica."""
    
    status = serializers.ChoiceField(
        choices=['DRAFT', 'PENDING', 'APPROVED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'SUSPENDED'],
        required=True
    )
    observaciones = serializers.CharField(required=False, allow_blank=True)
    calificacion_final = serializers.DecimalField(
        max_digits=4,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=0,
        max_value=20
    )
    
    def validate(self, attrs):
        """Validar transiciones de estado."""
        nuevo_estado = attrs['status']
        practica = self.context.get('practice')
        
        if not practica:
            return attrs
        
        estado_actual = practica.status
        
        # Validar transiciones permitidas
        transiciones_validas = {
            'DRAFT': ['PENDING'],
            'PENDING': ['APPROVED', 'CANCELLED'],
            'APPROVED': ['IN_PROGRESS', 'CANCELLED'],
            'IN_PROGRESS': ['COMPLETED', 'SUSPENDED', 'CANCELLED'],
            'SUSPENDED': ['IN_PROGRESS', 'CANCELLED'],
            'COMPLETED': [],  # No se puede cambiar
            'CANCELLED': []   # No se puede cambiar
        }
        
        if nuevo_estado not in transiciones_validas.get(estado_actual, []):
            raise serializers.ValidationError({
                'status': f'No se puede cambiar de {estado_actual} a {nuevo_estado}'
            })
        
        # Si se completa, requiere calificación
        if nuevo_estado == 'COMPLETED' and not attrs.get('calificacion_final'):
            raise serializers.ValidationError({
                'calificacion_final': 'Se requiere calificación para completar la práctica'
            })
        
        return attrs


# ============================================================================
# SERIALIZERS DE DOCUMENTOS (DOCUMENT)
# ============================================================================

class DocumentListSerializer(serializers.ModelSerializer):
    """Serializer simple para listar documentos."""
    
    practice = PracticeListSerializer(read_only=True)
    uploaded_by = UserListSerializer(source='subido_por', read_only=True)
    approved_by = UserListSerializer(source='aprobado_por', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'practice', 'tipo', 'archivo', 'nombre_archivo', 'uploaded_by',
            'aprobado', 'approved_by', 'fecha_aprobacion', 'file_size_mb',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_file_size_mb(self, obj):
        """Tamaño del archivo en MB."""
        if obj.archivo:
            try:
                size_bytes = obj.archivo.size
                return round(size_bytes / (1024 * 1024), 2)
            except:
                return None
        return None


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para documentos."""
    
    practice = PracticeDetailSerializer(read_only=True)
    uploaded_by = UserDetailSerializer(source='subido_por', read_only=True)
    approved_by = UserDetailSerializer(source='aprobado_por', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    file_extension = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'practice', 'tipo', 'archivo', 'nombre_archivo', 'uploaded_by',
            'aprobado', 'approved_by', 'fecha_aprobacion',
            'file_size_mb', 'file_extension', 'download_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_file_size_mb(self, obj):
        """Tamaño en MB."""
        if obj.archivo:
            try:
                return round(obj.archivo.size / (1024 * 1024), 2)
            except:
                return None
        return None
    
    def get_file_extension(self, obj):
        """Extensión del archivo."""
        if obj.archivo:
            return os.path.splitext(obj.archivo.name)[1].lower()
        return None
    
    def get_download_url(self, obj):
        """URL de descarga."""
        if obj.archivo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.archivo.url)
        return None


class DocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear documentos."""
    
    practice_id = serializers.UUIDField(write_only=True)
    archivo = serializers.FileField(required=True)
    
    class Meta:
        model = Document
        fields = ['practice_id', 'tipo', 'archivo', 'nombre_archivo']
    
    def validate_practice_id(self, value):
        """Validar que la práctica exista."""
        try:
            Practice.objects.get(id=value)
        except Practice.DoesNotExist:
            raise serializers.ValidationError('Práctica no encontrada')
        return value
    
    def validate_archivo(self, value):
        """Validar archivo."""
        # Tamaño máximo 10MB
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError('El archivo no puede superar los 10MB')
        
        # Extensiones permitidas
        ext = os.path.splitext(value.name)[1].lower()
        allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.zip']
        
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f'Extensión no permitida. Permitidas: {", ".join(allowed_extensions)}'
            )
        
        return value
    
    def create(self, validated_data):
        """Crear documento."""
        practice_id = validated_data.pop('practice_id')
        practice = Practice.objects.get(id=practice_id)
        
        # Usuario que sube
        user = self.context['request'].user
        
        # Si no se proporciona nombre, usar el del archivo
        if not validated_data.get('nombre_archivo'):
            validated_data['nombre_archivo'] = validated_data['archivo'].name
        
        document = Document.objects.create(
            practice=practice,
            uploaded_by=user,
            aprobado=False,
            **validated_data
        )
        return document


class DocumentUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar documentos."""
    
    archivo = serializers.FileField(required=False)
    
    class Meta:
        model = Document
        fields = ['tipo', 'archivo', 'nombre_archivo']
    
    def validate_archivo(self, value):
        """Validar archivo si se proporciona."""
        if value:
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError('El archivo no puede superar los 10MB')
            
            ext = os.path.splitext(value.name)[1].lower()
            allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.zip']
            
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    f'Extensión no permitida. Permitidas: {", ".join(allowed_extensions)}'
                )
        
        return value


class DocumentApproveSerializer(serializers.Serializer):
    """Serializer para aprobar/rechazar documentos."""
    
    aprobado = serializers.BooleanField(required=True)
    observaciones = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validar que si se rechaza, tenga observaciones."""
        if not attrs['aprobado'] and not attrs.get('observaciones'):
            raise serializers.ValidationError({
                'observaciones': 'Debe indicar el motivo del rechazo'
            })
        return attrs


# ============================================================================
# SERIALIZERS DE NOTIFICACIONES (NOTIFICATION)
# ============================================================================

class NotificationListSerializer(serializers.ModelSerializer):
    """Serializer simple para listar notificaciones."""
    
    user = UserListSerializer(read_only=True)
    time_since = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'tipo', 'titulo', 'mensaje', 'leida', 'time_since',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_time_since(self, obj):
        """Tiempo transcurrido desde la creación."""
        from django.utils.timesince import timesince
        return timesince(obj.created_at)


class NotificationDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para notificaciones."""
    
    user = UserDetailSerializer(read_only=True)
    time_since = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'tipo', 'titulo', 'mensaje', 'leida', 'fecha_lectura',
            'accion_url', 'time_since',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_time_since(self, obj):
        """Tiempo transcurrido."""
        from django.utils.timesince import timesince
        return timesince(obj.created_at)


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear notificaciones."""
    
    user_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'user_id', 'tipo', 'titulo', 'mensaje', 'accion_url'
        ]
    
    def validate_user_id(self, value):
        """Validar usuario."""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('Usuario no encontrado')
        return value
    
    def create(self, validated_data):
        """Crear notificación."""
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)
        
        notification = Notification.objects.create(
            user=user,
            leida=False,
            **validated_data
        )
        return notification


class NotificationMarkAsReadSerializer(serializers.Serializer):
    """Serializer para marcar notificaciones como leídas."""
    
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        allow_empty=False
    )
    
    def validate_notification_ids(self, value):
        """Validar que las notificaciones existan."""
        user = self.context['request'].user
        
        notifications = Notification.objects.filter(
            id__in=value,
            user=user
        )
        
        if notifications.count() != len(value):
            raise serializers.ValidationError(
                'Algunas notificaciones no fueron encontradas o no te pertenecen'
            )
        
        return value


# ============================================================================
# SERIALIZERS AUXILIARES PARA BÚSQUEDAS Y FILTROS
# ============================================================================

class PracticeSearchSerializer(serializers.Serializer):
    """Serializer para búsqueda avanzada de prácticas."""
    
    student_codigo = serializers.CharField(required=False)
    company_ruc = serializers.CharField(required=False)
    status = serializers.ChoiceField(
        choices=['DRAFT', 'PENDING', 'APPROVED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'SUSPENDED'],
        required=False
    )
    modalidad = serializers.ChoiceField(
        choices=['PRESENCIAL', 'REMOTO', 'HIBRIDO'],
        required=False
    )
    fecha_inicio_desde = serializers.DateField(required=False)
    fecha_inicio_hasta = serializers.DateField(required=False)
    fecha_fin_desde = serializers.DateField(required=False)
    fecha_fin_hasta = serializers.DateField(required=False)
    area_practica = serializers.CharField(required=False)


class StudentSearchSerializer(serializers.Serializer):
    """Serializer para búsqueda de estudiantes."""
    
    codigo = serializers.CharField(required=False)
    escuela = serializers.CharField(required=False)
    semestre_min = serializers.IntegerField(required=False, min_value=1, max_value=12)
    promedio_min = serializers.DecimalField(
        required=False,
        max_digits=4,
        decimal_places=2,
        min_value=0,
        max_value=20
    )
    puede_realizar_practica = serializers.BooleanField(required=False)


class CompanySearchSerializer(serializers.Serializer):
    """Serializer para búsqueda de empresas."""
    
    ruc = serializers.CharField(required=False)
    sector = serializers.CharField(required=False)
    status = serializers.ChoiceField(
        choices=['PENDING_VALIDATION', 'ACTIVE', 'SUSPENDED', 'INACTIVE'],
        required=False
    )
    puede_recibir_practicantes = serializers.BooleanField(required=False)


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas del dashboard."""
    
    total_students = serializers.IntegerField()
    total_companies = serializers.IntegerField()
    total_practices = serializers.IntegerField()
    active_practices = serializers.IntegerField()
    completed_practices = serializers.IntegerField()
    pending_documents = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    practices_by_status = serializers.DictField()
    practices_by_modalidad = serializers.DictField()
    top_companies = serializers.ListField()
    recent_practices = PracticeListSerializer(many=True)


# ============================================================================
# FIN DE SERIALIZERS
# ============================================================================
