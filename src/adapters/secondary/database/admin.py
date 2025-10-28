"""
Configuración del admin de Django para gestión de usuarios.
Permite administrar usuarios con cambio de roles, estados, etc.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    User, 
    Role, 
    Avatar,
    StudentProfile,
    SupervisorProfile,
    CoordinatorSchool,
    SecretariaProfile,
    AdminProfile,
    SuperAdminProfile
)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """
    Admin personalizado para el modelo User.
    Permite gestionar todos los usuarios con sus roles y estados.
    """
    
    # Campos a mostrar en la lista de usuarios
    list_display = (
        'correo',
        'get_full_name',
        'dni',
        'get_role_display',
        'activo',
        'fecha_creacion',
        'ultimo_acceso',
        'actions_column'
    )
    
    # Campos por los que se puede buscar
    search_fields = ('correo', 'dni', 'nombres', 'apellidos', 'telefono')
    
    # Filtros laterales
    list_filter = (
        'activo',
        'rol_id',
        'fecha_creacion',
        'ultimo_acceso'
    )
    
    # Ordenamiento por defecto
    ordering = ('-fecha_creacion',)
    
    # Campos de solo lectura
    readonly_fields = (
        'id',
        'fecha_creacion',
        'ultimo_acceso',
        'creado_por',
        'get_profile_info'
    )
    
    # Organización de campos en el formulario de edición
    fieldsets = (
        ('Información de Autenticación', {
            'fields': ('correo', 'hash_contraseña')
        }),
        ('Información Personal', {
            'fields': ('dni', 'nombres', 'apellidos', 'telefono')
        }),
        ('Rol y Estado', {
            'fields': ('rol_id', 'escuela_id', 'activo'),
            'description': 'Configure el rol del usuario y su estado en el sistema'
        }),
        ('Fechas Importantes', {
            'fields': (
                'fecha_creacion',
                'ultimo_acceso',
                'creado_por'
            ),
            'classes': ('collapse',)
        }),
        ('Información del Perfil', {
            'fields': ('get_profile_info',),
            'classes': ('collapse',)
        }),
    )
    
    # Campos para crear nuevo usuario
    add_fieldsets = (
        ('Información de Autenticación', {
            'classes': ('wide',),
            'fields': ('correo', 'hash_contraseña'),
        }),
        ('Información Personal', {
            'fields': ('dni', 'nombres', 'apellidos', 'telefono')
        }),
        ('Rol', {
            'fields': ('rol_id', 'escuela_id', 'activo')
        }),
    )
    
    # Acciones masivas personalizadas
    actions = [
        'activate_users',
        'deactivate_users',
    ]
    
    def get_full_name(self, obj):
        """Retorna el nombre completo del usuario."""
        return obj.get_full_name()
    get_full_name.short_description = 'Nombre Completo'
    
    def get_role_display(self, obj):
        """Muestra el rol con color según el tipo."""
        if not obj.rol_id:
            return format_html('<span style="color: gray;">Sin Rol</span>')
        
        colors = {
            'PRACTICANTE': '#3498db',      # Azul
            'SUPERVISOR': '#2ecc71',       # Verde
            'COORDINADOR': '#f39c12',      # Naranja
            'SECRETARIA': '#9b59b6',       # Morado
            'ADMINISTRADOR': '#e74c3c',    # Rojo
        }
        
        color = colors.get(obj.rol_id.nombre, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.rol_id.nombre
        )
    get_role_display.short_description = 'Rol'
    
    def get_profile_info(self, obj):
        """Muestra información del perfil específico según el rol."""
        if not obj.rol_id:
            return "Sin rol asignado"
        
        profile_info = []
        
        try:
            if obj.rol_id.nombre == 'PRACTICANTE' and hasattr(obj, 'student_profile'):
                profile = obj.student_profile
                profile_info.append(f"<strong>Código:</strong> {profile.codigo}")
                profile_info.append(f"<strong>Semestre:</strong> {profile.semestre}")
                profile_info.append(f"<strong>Promedio:</strong> {profile.promedio_ponderado}")
                profile_info.append(f"<strong>Horas Prácticas:</strong> {profile.horas_practicas_acumuladas}")
                
            elif obj.rol_id.nombre == 'SUPERVISOR' and hasattr(obj, 'supervisor_profile'):
                profile = obj.supervisor_profile
                profile_info.append(f"<strong>Cargo:</strong> {profile.cargo}")
                if profile.empresa:
                    profile_info.append(f"<strong>Empresa:</strong> {profile.empresa.nombre}")
                
            elif obj.rol_id.nombre == 'COORDINADOR' and hasattr(obj, 'coordinator_assignments'):
                assignments = obj.coordinator_assignments.filter(activo=True)
                if assignments.exists():
                    escuelas = ', '.join([a.escuela.nombre for a in assignments])
                    profile_info.append(f"<strong>Escuelas:</strong> {escuelas}")
                
            elif obj.rol_id.nombre == 'SECRETARIA' and hasattr(obj, 'secretaria_profile'):
                profile = obj.secretaria_profile
                profile_info.append(f"<strong>Código Empleado:</strong> {profile.codigo_empleado}")
                
            elif obj.rol_id.nombre == 'ADMINISTRADOR' and hasattr(obj, 'admin_profile'):
                profile = obj.admin_profile
                profile_info.append(f"<strong>Nivel Acceso:</strong> {profile.nivel_acceso}")
                
        except Exception as e:
            return f"Error al cargar perfil: {str(e)}"
        
        if profile_info:
            return mark_safe('<br>'.join(profile_info))
        return "Sin perfil específico"
    
    get_profile_info.short_description = 'Información del Perfil'
    
    def actions_column(self, obj):
        """Columna con acciones rápidas."""
        actions = []
        
        # Botón para ver detalles
        detail_url = reverse('admin:database_user_change', args=[obj.pk])
        actions.append(f'<a class="button" href="{detail_url}">Ver/Editar</a>')
        
        return mark_safe(' '.join(actions))
    
    actions_column.short_description = 'Acciones'
    
    # ========== Acciones Masivas ==========
    
    def activate_users(self, request, queryset):
        """Activa los usuarios seleccionados."""
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} usuario(s) activado(s) correctamente.')
    activate_users.short_description = '✅ Activar usuarios seleccionados'
    
    def deactivate_users(self, request, queryset):
        """Desactiva los usuarios seleccionados."""
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} usuario(s) desactivado(s) correctamente.')
    deactivate_users.short_description = '❌ Desactivar usuarios seleccionados'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin para gestión de roles."""
    
    list_display = ('nombre', 'descripcion', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('id', 'fecha_creacion')
    
    fieldsets = (
        ('Información del Rol', {
            'fields': ('nombre', 'descripcion', 'permisos')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Avatar)
class AvatarAdmin(admin.ModelAdmin):
    """Admin para gestión de avatares."""
    
    list_display = ('id', 'role', 'url', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')
    search_fields = ('url',)
    readonly_fields = ('id', 'created_at')


# Personalización del sitio admin
admin.site.site_header = 'Sistema de Gestión de Prácticas Profesionales - UPeU'
admin.site.site_title = 'Admin Prácticas UPeU'
admin.site.index_title = 'Panel de Administración'
