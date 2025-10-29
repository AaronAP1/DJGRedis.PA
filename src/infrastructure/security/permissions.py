"""
Sistema de permisos granular basado en roles para el sistema de gestión de prácticas.

Roles del sistema:
- PRACTICANTE: Estudiante realizando prácticas
- SUPERVISOR: Supervisor de empresa
- COORDINADOR: Coordinador académico
- SECRETARIA: Personal administrativo
- ADMINISTRADOR: Administrador del sistema
"""

from rest_framework import permissions


# ============================================================================
# HELPER FUNCTION - Obtener rol del usuario
# ============================================================================

def get_user_role(user):
    """
    Obtiene el rol del usuario desde rol_id.nombre.
    El modelo User tiene rol_id (FK a upeu_rol), no un campo 'role' directo.
    
    Returns:
        str: Nombre del rol ('ADMINISTRADOR', 'COORDINADOR', etc.) o None
    """
    if not user or not user.is_authenticated:
        return None
    
    # user.rol_id es FK a Role (upeu_rol)
    if hasattr(user, 'rol_id') and user.rol_id:
        return user.rol_id.nombre  # upeu_rol.nombre
    
    # Fallback: si es superuser, considerarlo ADMINISTRADOR
    if user.is_superuser:
        return 'ADMINISTRADOR'
    
    return None


# ============================================================================
# PERMISOS BASE POR ROL
# ============================================================================

class IsAuthenticated(permissions.BasePermission):
    """Verifica que el usuario esté autenticado."""
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsAdministrador(permissions.BasePermission):
    """Permite acceso solo a ADMINISTRADOR."""

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            get_user_role(request.user) == 'ADMINISTRADOR'
        )


class IsPracticante(permissions.BasePermission):
    """Permite acceso solo a PRACTICANTE."""

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            get_user_role(request.user) == 'PRACTICANTE'
        )


class IsSupervisor(permissions.BasePermission):
    """Permite acceso solo a SUPERVISOR."""

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            get_user_role(request.user) == 'SUPERVISOR'
        )


class IsCoordinador(permissions.BasePermission):
    """Permite acceso solo a COORDINADOR."""

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            get_user_role(request.user) == 'COORDINADOR'
        )


class IsSecretaria(permissions.BasePermission):
    """Permite acceso solo a SECRETARIA."""

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            get_user_role(request.user) == 'SECRETARIA'
        )


# ============================================================================
# PERMISOS COMBINADOS POR ROL
# ============================================================================

class IsAdminOrCoordinador(permissions.BasePermission):
    """Permite acceso a ADMINISTRADOR o COORDINADOR."""

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR']
        )


class IsAdminOrCoordinadorOrSecretaria(permissions.BasePermission):
    """Permite acceso a ADMINISTRADOR, COORDINADOR o SECRETARIA."""

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']
        )


class IsStaffMember(permissions.BasePermission):
    """Permite acceso a personal administrativo (COORDINADOR, SECRETARIA, ADMIN)."""

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']
        )


# ============================================================================
# PERMISOS DE PROPIEDAD (OWNERSHIP)
# ============================================================================

class IsOwner(permissions.BasePermission):
    """Verifica que el usuario sea el propietario del objeto."""

    def has_object_permission(self, request, view, obj):
        # Si el objeto tiene un atributo 'user', verificar que sea el mismo
        if hasattr(obj, 'user'):
            return obj.user == request.user
        # Si el objeto ES el usuario
        if hasattr(obj, 'email'):
            return obj == request.user
        return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permite acceso al propietario o a ADMINISTRADOR."""

    def has_object_permission(self, request, view, obj):
        # ADMINISTRADOR tiene acceso total
        if get_user_role(request.user) == 'ADMINISTRADOR':
            return True
        
        # Verificar propiedad
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'email'):
            return obj == request.user
        return False


class IsOwnerOrStaff(permissions.BasePermission):
    """Permite acceso al propietario o al personal administrativo."""

    def has_object_permission(self, request, view, obj):
        # Personal administrativo tiene acceso
        if get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']:
            return True
        
        # Verificar propiedad
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'email'):
            return obj == request.user
        return False


# ============================================================================
# PERMISOS ESPECÍFICOS PARA USUARIOS
# ============================================================================

class CanManageUsers(permissions.BasePermission):
    """Permite gestionar usuarios (crear, editar, eliminar)."""

    def has_permission(self, request, view):
        # Solo ADMIN, COORDINADOR y SECRETARIA pueden gestionar usuarios
        return bool(
            request.user and 
            request.user.is_authenticated and 
            get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']
        )

    def has_object_permission(self, request, view, obj):
        # ADMINISTRADOR puede hacer todo
        if get_user_role(request.user) == 'ADMINISTRADOR':
            return True
        
        # COORDINADOR y SECRETARIA pueden gestionar excepto ADMIN
        if get_user_role(request.user) in ['COORDINADOR', 'SECRETARIA']:
            return get_user_role(obj) != 'ADMINISTRADOR'
        
        return False


class CanViewOwnProfile(permissions.BasePermission):
    """Permite ver solo el propio perfil."""

    def has_object_permission(self, request, view, obj):
        # Solo métodos seguros (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return obj == request.user or get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']
        return False


class CanUpdateOwnProfile(permissions.BasePermission):
    """Permite actualizar solo el propio perfil."""

    def has_object_permission(self, request, view, obj):
        # Puede actualizar su propio perfil
        if obj == request.user:
            return True
        
        # Staff puede actualizar perfiles
        if get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']:
            return True
        
        return False


# ============================================================================
# PERMISOS ESPECÍFICOS PARA ESTUDIANTES
# ============================================================================

class CanManageStudents(permissions.BasePermission):
    """Permite gestionar estudiantes."""

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']
        )


class CanViewStudent(permissions.BasePermission):
    """Permite ver información de estudiantes."""

    def has_object_permission(self, request, view, obj):
        # Staff puede ver todos
        if get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']:
            return True
        
        # Estudiante puede ver su propio perfil
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # Supervisor puede ver estudiantes asignados
        if get_user_role(request.user) == 'SUPERVISOR':
            # Verificar si tiene prácticas con este estudiante
            if hasattr(request.user, 'supervisor_profile'):
                return obj.practices.filter(
                    supervisor=request.user.supervisor_profile
                ).exists()
        
        return False


# ============================================================================
# PERMISOS ESPECÍFICOS PARA EMPRESAS
# ============================================================================

class CanManageCompanies(permissions.BasePermission):
    """Permite gestionar empresas."""

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']
        )


class CanViewCompany(permissions.BasePermission):
    """Permite ver información de empresas."""

    def has_object_permission(self, request, view, obj):
        # Staff y practicantes pueden ver todas las empresas activas
        if obj.status == 'ACTIVE':
            return True
        
        # Staff puede ver todas
        if get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']:
            return True
        
        # Supervisor puede ver su propia empresa
        if get_user_role(request.user) == 'SUPERVISOR':
            if hasattr(request.user, 'supervisor_profile'):
                return obj == request.user.supervisor_profile.company
        
        return False


class CanValidateCompany(permissions.BasePermission):
    """Permite validar/aprobar empresas."""

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR']
        )


# ============================================================================
# PERMISOS ESPECÍFICOS PARA PRÁCTICAS
# ============================================================================

class CanCreatePractice(permissions.BasePermission):
    """Permite crear prácticas."""

    def has_permission(self, request, view):
        # PRACTICANTE puede crear sus propias prácticas
        if get_user_role(request.user) == 'PRACTICANTE':
            return True
        
        # Staff puede crear prácticas para estudiantes
        if get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']:
            return True
        
        return False


class CanViewPractice(permissions.BasePermission):
    """Permite ver prácticas."""

    def has_object_permission(self, request, view, obj):
        # Staff puede ver todas
        if get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']:
            return True
        
        # Practicante puede ver sus propias prácticas
        if get_user_role(request.user) == 'PRACTICANTE':
            if hasattr(obj, 'student') and hasattr(obj.student, 'user'):
                return obj.student.user == request.user
        
        # Supervisor puede ver prácticas asignadas
        if get_user_role(request.user) == 'SUPERVISOR':
            if hasattr(request.user, 'supervisor_profile'):
                return obj.supervisor == request.user.supervisor_profile
        
        return False


class CanUpdatePractice(permissions.BasePermission):
    """Permite actualizar prácticas."""

    def has_object_permission(self, request, view, obj):
        # ADMINISTRADOR puede actualizar cualquier práctica
        if get_user_role(request.user) == 'ADMINISTRADOR':
            return True
        
        # COORDINADOR puede actualizar cualquier práctica
        if get_user_role(request.user) == 'COORDINADOR':
            return True
        
        # SECRETARIA puede actualizar datos básicos
        if get_user_role(request.user) == 'SECRETARIA':
            return True
        
        # PRACTICANTE solo puede actualizar si está en DRAFT
        if get_user_role(request.user) == 'PRACTICANTE':
            if hasattr(obj, 'student') and hasattr(obj.student, 'user'):
                return obj.student.user == request.user and obj.status == 'DRAFT'
        
        # SUPERVISOR puede actualizar prácticas asignadas (evaluación)
        if get_user_role(request.user) == 'SUPERVISOR':
            if hasattr(request.user, 'supervisor_profile'):
                return obj.supervisor == request.user.supervisor_profile
        
        return False


class CanApprovePractice(permissions.BasePermission):
    """Permite aprobar/rechazar prácticas."""

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR']
        )


class CanEvaluatePractice(permissions.BasePermission):
    """Permite evaluar prácticas (calificar)."""

    def has_object_permission(self, request, view, obj):
        # COORDINADOR puede evaluar
        if get_user_role(request.user) == 'COORDINADOR':
            return True
        
        # SUPERVISOR puede evaluar sus prácticas asignadas
        if get_user_role(request.user) == 'SUPERVISOR':
            if hasattr(request.user, 'supervisor_profile'):
                return obj.supervisor == request.user.supervisor_profile
        
        return False


# ============================================================================
# PERMISOS ESPECÍFICOS PARA DOCUMENTOS
# ============================================================================

class CanUploadDocument(permissions.BasePermission):
    """Permite subir documentos."""

    def has_permission(self, request, view):
        # PRACTICANTE puede subir documentos a sus prácticas
        if get_user_role(request.user) == 'PRACTICANTE':
            return True
        
        # Staff puede subir documentos
        if get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']:
            return True
        
        return False


class CanViewDocument(permissions.BasePermission):
    """Permite ver documentos."""

    def has_object_permission(self, request, view, obj):
        # Staff puede ver todos
        if get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']:
            return True
        
        # Practicante puede ver documentos de sus prácticas
        if get_user_role(request.user) == 'PRACTICANTE':
            if hasattr(obj, 'practice') and hasattr(obj.practice, 'student'):
                if hasattr(obj.practice.student, 'user'):
                    return obj.practice.student.user == request.user
        
        # Supervisor puede ver documentos de prácticas asignadas
        if get_user_role(request.user) == 'SUPERVISOR':
            if hasattr(request.user, 'supervisor_profile'):
                if hasattr(obj, 'practice'):
                    return obj.practice.supervisor == request.user.supervisor_profile
        
        return False


class CanDeleteDocument(permissions.BasePermission):
    """Permite eliminar documentos."""

    def has_object_permission(self, request, view, obj):
        # ADMINISTRADOR puede eliminar cualquier documento
        if get_user_role(request.user) == 'ADMINISTRADOR':
            return True
        
        # Practicante puede eliminar sus propios documentos si no están aprobados
        if get_user_role(request.user) == 'PRACTICANTE':
            if hasattr(obj, 'subido_por') and obj.subido_por == request.user:
                return not obj.aprobado
        
        return False


class CanApproveDocument(permissions.BasePermission):
    """Permite aprobar/rechazar documentos."""

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']
        )


# ============================================================================
# PERMISOS ESPECÍFICOS PARA NOTIFICACIONES
# ============================================================================

class CanViewNotification(permissions.BasePermission):
    """Permite ver notificaciones."""

    def has_object_permission(self, request, view, obj):
        # Solo puede ver sus propias notificaciones
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Staff puede ver todas
        if get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']:
            return True
        
        return False


class CanCreateNotification(permissions.BasePermission):
    """Permite crear notificaciones."""

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']
        )


# ============================================================================
# PERMISOS COMBINADOS Y DE SOLO LECTURA
# ============================================================================

class ReadOnly(permissions.BasePermission):
    """Permite solo operaciones de lectura."""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsAuthenticatedReadOnly(permissions.BasePermission):
    """Permite lectura a usuarios autenticados, escritura a staff."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        
        return bool(
            request.user and 
            request.user.is_authenticated and 
            get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']
        )


# ============================================================================
# PERMISOS LEGACY (compatibilidad con código anterior)
# ============================================================================

class IsAdminOnly(permissions.BasePermission):
    """Permite acceso solo a ADMINISTRADOR (legacy)."""

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            get_user_role(request.user) == 'ADMINISTRADOR'
        )


class IsAdminOrCoordinatorOrSecretary(permissions.BasePermission):
    """Permite acceso a ADMINISTRADOR, COORDINADOR o SECRETARIA (legacy)."""

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            get_user_role(request.user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']
        )
