"""
Helpers para verificación de permisos en GraphQL y otros contextos.

Estos helpers complementan las clases de permisos de DRF y pueden
ser utilizados en resolvers de GraphQL, tareas de Celery, etc.
"""

from typing import Optional
from django.contrib.auth import get_user_model

User = get_user_model()


# ============================================================================
# HELPER PARA OBTENER ROL
# ============================================================================

def get_user_role(user) -> str:
    """
    Obtiene el rol del usuario de manera segura.
    
    Args:
        user: Usuario de Django
        
    Returns:
        str: Nombre del rol o 'ADMINISTRADOR' si es superuser
    """
    if not user or not user.is_authenticated:
        return ''
    
    if user.is_superuser:
        return 'ADMINISTRADOR'
    
    try:
        return user.rol_id.nombre if user.rol_id else ''
    except Exception:
        return ''


# ============================================================================
# VERIFICADORES DE ROL
# ============================================================================

def is_administrador(user) -> bool:
    """Verifica si el usuario es ADMINISTRADOR."""
    return user and user.is_authenticated and get_user_role(user) == 'ADMINISTRADOR'


def is_coordinador(user) -> bool:
    """Verifica si el usuario es COORDINADOR."""
    return user and user.is_authenticated and get_user_role(user) == 'COORDINADOR'


def is_secretaria(user) -> bool:
    """Verifica si el usuario es SECRETARIA."""
    return user and user.is_authenticated and get_user_role(user) == 'SECRETARIA'


def is_supervisor(user) -> bool:
    """Verifica si el usuario es SUPERVISOR."""
    return user and user.is_authenticated and get_user_role(user) == 'SUPERVISOR'


def is_practicante(user) -> bool:
    """Verifica si el usuario es PRACTICANTE."""
    return user and user.is_authenticated and get_user_role(user) == 'PRACTICANTE'


def is_staff(user) -> bool:
    """Verifica si el usuario es personal administrativo."""
    return user and user.is_authenticated and get_user_role(user) in [
        'ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA'
    ]


# ============================================================================
# VERIFICADORES DE PERMISOS SOBRE USUARIOS
# ============================================================================

def can_view_user(user, target_user) -> bool:
    """Verifica si el usuario puede ver el perfil de otro usuario."""
    if not user or not user.is_authenticated:
        return False
    
    # Puede ver su propio perfil
    if user == target_user:
        return True
    
    # Staff puede ver todos los perfiles
    if is_staff(user):
        return True
    
    return False


def can_update_user(user, target_user) -> bool:
    """Verifica si el usuario puede actualizar otro usuario."""
    if not user or not user.is_authenticated:
        return False
    
    # Puede actualizar su propio perfil
    if user == target_user:
        return True
    
    # ADMINISTRADOR puede actualizar cualquier usuario
    if is_administrador(user):
        return True
    
    # COORDINADOR y SECRETARIA pueden actualizar excepto ADMINISTRADOR
    user_role = get_user_role(user)
    target_role = get_user_role(target_user)
    if user_role in ['COORDINADOR', 'SECRETARIA']:
        return target_role != 'ADMINISTRADOR'
    
    return False


def can_delete_user(user, target_user) -> bool:
    """Verifica si el usuario puede eliminar otro usuario."""
    if not user or not user.is_authenticated:
        return False
    
    # Solo ADMINISTRADOR puede eliminar usuarios
    return is_administrador(user)


# ============================================================================
# VERIFICADORES DE PERMISOS SOBRE ESTUDIANTES
# ============================================================================

def can_create_student(user) -> bool:
    """Verifica si el usuario puede crear estudiantes."""
    if not user or not user.is_authenticated:
        return False
    
    # Solo staff puede crear estudiantes
    return is_staff(user)


def can_view_student(user, student) -> bool:
    """Verifica si el usuario puede ver información del estudiante."""
    if not user or not user.is_authenticated:
        return False
    
    # Staff puede ver todos
    if is_staff(user):
        return True
    
    # Estudiante puede ver su propio perfil
    if hasattr(student, 'user') and student.user == user:
        return True
    
    # Supervisor puede ver estudiantes con prácticas asignadas
    if is_supervisor(user) and hasattr(user, 'supervisor_profile'):
        return student.practices.filter(supervisor=user.supervisor_profile).exists()
    
    return False


def can_update_student(user, student) -> bool:
    """Verifica si el usuario puede actualizar información del estudiante."""
    if not user or not user.is_authenticated:
        return False
    
    # Staff puede actualizar
    if is_staff(user):
        return True
    
    # Estudiante puede actualizar su propio perfil
    if hasattr(student, 'user') and student.user == user:
        return True
    
    return False


def can_delete_student(user, student) -> bool:
    """Verifica si el usuario puede eliminar un estudiante."""
    if not user or not user.is_authenticated:
        return False
    
    # Solo ADMINISTRADOR puede eliminar
    return is_administrador(user)


# ============================================================================
# VERIFICADORES DE PERMISOS SOBRE EMPRESAS
# ============================================================================

def can_create_company(user) -> bool:
    """Verifica si el usuario puede crear empresas."""
    if not user or not user.is_authenticated:
        return False
    
    # Staff y supervisores pueden crear empresas
    return is_staff(user) or is_supervisor(user)


def can_view_company(user, company) -> bool:
    """Verifica si el usuario puede ver información de la empresa."""
    if not user or not user.is_authenticated:
        return False
    
    # Empresas activas pueden ser vistas por todos
    if company.status == 'ACTIVE':
        return True
    
    # Staff puede ver todas
    if is_staff(user):
        return True
    
    # Supervisor puede ver su propia empresa
    if is_supervisor(user) and hasattr(user, 'supervisor_profile'):
        return company == user.supervisor_profile.company
    
    return False


def can_update_company(user, company) -> bool:
    """Verifica si el usuario puede actualizar la empresa."""
    if not user or not user.is_authenticated:
        return False
    
    # Staff puede actualizar
    if is_staff(user):
        return True
    
    # Supervisor puede actualizar su propia empresa
    if is_supervisor(user) and hasattr(user, 'supervisor_profile'):
        return company == user.supervisor_profile.company
    
    return False


def can_validate_company(user) -> bool:
    """Verifica si el usuario puede validar empresas."""
    if not user or not user.is_authenticated:
        return False
    
    return get_user_role(user) in ['ADMINISTRADOR', 'COORDINADOR']


# ============================================================================
# VERIFICADORES DE PERMISOS SOBRE SUPERVISORES
# ============================================================================

def can_create_supervisor(user) -> bool:
    """Verifica si el usuario puede crear supervisores."""
    if not user or not user.is_authenticated:
        return False
    
    # Solo staff puede crear supervisores
    return is_staff(user)


def can_update_supervisor(user, supervisor) -> bool:
    """Verifica si el usuario puede actualizar el supervisor."""
    if not user or not user.is_authenticated:
        return False
    
    # Staff puede actualizar
    if is_staff(user):
        return True
    
    # Supervisor puede actualizar su propio perfil
    if hasattr(supervisor, 'user') and supervisor.user == user:
        return True
    
    return False


# ============================================================================
# VERIFICADORES DE PERMISOS SOBRE PRÁCTICAS
# ============================================================================

def can_create_practice(user) -> bool:
    """Verifica si el usuario puede crear prácticas."""
    if not user or not user.is_authenticated:
        return False
    
    # Staff y practicantes pueden crear prácticas
    return is_staff(user) or is_practicante(user)


def can_view_practice(user, practice) -> bool:
    """Verifica si el usuario puede ver la práctica."""
    if not user or not user.is_authenticated:
        return False
    
    # Staff puede ver todas
    if is_staff(user):
        return True
    
    # Practicante puede ver sus propias prácticas
    if is_practicante(user) and hasattr(practice, 'student'):
        if hasattr(practice.student, 'user'):
            return practice.student.user == user
    
    # Supervisor puede ver prácticas asignadas
    if is_supervisor(user) and hasattr(user, 'supervisor_profile'):
        return practice.supervisor == user.supervisor_profile
    
    return False


def can_update_practice(user, practice) -> bool:
    """Verifica si el usuario puede actualizar la práctica."""
    if not user or not user.is_authenticated:
        return False
    
    # ADMINISTRADOR y COORDINADOR pueden actualizar cualquier práctica
    if get_user_role(user) in ['ADMINISTRADOR', 'COORDINADOR']:
        return True
    
    # SECRETARIA puede actualizar datos básicos
    if is_secretaria(user):
        return True
    
    # PRACTICANTE solo puede actualizar si está en DRAFT
    if is_practicante(user) and hasattr(practice, 'student'):
        if hasattr(practice.student, 'user'):
            return practice.student.user == user and practice.status == 'DRAFT'
    
    # SUPERVISOR puede actualizar prácticas asignadas
    if is_supervisor(user) and hasattr(user, 'supervisor_profile'):
        return practice.supervisor == user.supervisor_profile
    
    return False


def can_approve_practice(user) -> bool:
    """Verifica si el usuario puede aprobar prácticas."""
    if not user or not user.is_authenticated:
        return False
    
    return get_user_role(user) in ['ADMINISTRADOR', 'COORDINADOR']


def can_evaluate_practice(user, practice) -> bool:
    """Verifica si el usuario puede evaluar/calificar la práctica."""
    if not user or not user.is_authenticated:
        return False
    
    # COORDINADOR puede evaluar
    if is_coordinador(user):
        return True
    
    # SUPERVISOR puede evaluar sus prácticas asignadas
    if is_supervisor(user) and hasattr(user, 'supervisor_profile'):
        return practice.supervisor == user.supervisor_profile
    
    return False


def can_change_practice_status(user, practice, new_status: str) -> bool:
    """Verifica si el usuario puede cambiar el estado de la práctica."""
    if not user or not user.is_authenticated:
        return False
    
    # ADMINISTRADOR puede cambiar cualquier estado
    if is_administrador(user):
        return True
    
    # COORDINADOR puede aprobar/rechazar
    if is_coordinador(user):
        return new_status in ['APPROVED', 'PENDING', 'CANCELLED', 'SUSPENDED']
    
    # PRACTICANTE solo puede pasar de DRAFT a PENDING
    if is_practicante(user) and hasattr(practice, 'student'):
        if hasattr(practice.student, 'user') and practice.student.user == user:
            return practice.status == 'DRAFT' and new_status == 'PENDING'
    
    # SUPERVISOR puede iniciar y completar prácticas asignadas
    if is_supervisor(user) and hasattr(user, 'supervisor_profile'):
        if practice.supervisor == user.supervisor_profile:
            return new_status in ['IN_PROGRESS', 'COMPLETED']
    
    return False


# ============================================================================
# VERIFICADORES DE PERMISOS SOBRE DOCUMENTOS
# ============================================================================

def can_view_document(user, document) -> bool:
    """Verifica si el usuario puede ver el documento."""
    if not user or not user.is_authenticated:
        return False
    
    # Staff puede ver todos
    if is_staff(user):
        return True
    
    # Practicante puede ver documentos de sus prácticas
    if is_practicante(user) and hasattr(document, 'practice'):
        if hasattr(document.practice, 'student') and hasattr(document.practice.student, 'user'):
            return document.practice.student.user == user
    
    # Supervisor puede ver documentos de prácticas asignadas
    if is_supervisor(user) and hasattr(user, 'supervisor_profile'):
        if hasattr(document, 'practice'):
            return document.practice.supervisor == user.supervisor_profile
    
    return False


def can_upload_document(user, practice) -> bool:
    """Verifica si el usuario puede subir documentos a la práctica."""
    if not user or not user.is_authenticated:
        return False
    
    # Staff puede subir
    if is_staff(user):
        return True
    
    # Practicante puede subir a sus propias prácticas
    if is_practicante(user) and hasattr(practice, 'student'):
        if hasattr(practice.student, 'user'):
            return practice.student.user == user
    
    return False


def can_delete_document(user, document) -> bool:
    """Verifica si el usuario puede eliminar el documento."""
    if not user or not user.is_authenticated:
        return False
    
    # ADMINISTRADOR puede eliminar cualquier documento
    if is_administrador(user):
        return True
    
    # Practicante puede eliminar sus propios documentos si no están aprobados
    if is_practicante(user) and hasattr(document, 'subido_por'):
        return document.subido_por == user and not document.aprobado
    
    return False


def can_approve_document(user) -> bool:
    """Verifica si el usuario puede aprobar documentos."""
    if not user or not user.is_authenticated:
        return False
    
    return get_user_role(user) in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']


# ============================================================================
# VERIFICADORES DE PERMISOS SOBRE NOTIFICACIONES
# ============================================================================

def can_view_notification(user, notification) -> bool:
    """Verifica si el usuario puede ver la notificación."""
    if not user or not user.is_authenticated:
        return False
    
    # Puede ver sus propias notificaciones
    if hasattr(notification, 'user'):
        return notification.user == user
    
    # Staff puede ver todas
    if is_staff(user):
        return True
    
    return False


def can_create_notification(user) -> bool:
    """Verifica si el usuario puede crear notificaciones."""
    if not user or not user.is_authenticated:
        return False
    
    return is_staff(user)


# ============================================================================
# VERIFICADORES DE ACCESO A REPORTES Y DASHBOARD
# ============================================================================

def can_view_all_statistics(user) -> bool:
    """Verifica si el usuario puede ver estadísticas globales."""
    if not user or not user.is_authenticated:
        return False
    
    return is_staff(user)


def can_view_reports(user) -> bool:
    """Verifica si el usuario puede ver reportes."""
    if not user or not user.is_authenticated:
        return False
    
    return is_staff(user)


def can_export_data(user) -> bool:
    """Verifica si el usuario puede exportar datos."""
    if not user or not user.is_authenticated:
        return False
    
    return is_staff(user)


# ============================================================================
# UTILIDADES GENERALES
# ============================================================================

def get_user_role(user) -> Optional[str]:
    """Retorna el rol del usuario o None."""
    if user and user.is_authenticated:
        return getattr(user, 'role', None)
    return None


def has_any_role(user, roles: list) -> bool:
    """Verifica si el usuario tiene alguno de los roles especificados."""
    if not user or not user.is_authenticated:
        return False
    
    user_role = get_user_role(user)
    return user_role in roles


def require_authentication(user) -> bool:
    """Verifica que el usuario esté autenticado."""
    return bool(user and user.is_authenticated)


# ============================================================================
# VERIFICADORES DE PERMISOS PARA LISTADOS/COLECCIONES
# ============================================================================

def can_view_users(user) -> bool:
    """Verifica si el usuario puede ver el listado de usuarios."""
    if not user or not user.is_authenticated:
        return False
    # Solo staff puede ver listado de usuarios
    return is_staff(user)


def can_view_students(user) -> bool:
    """Verifica si el usuario puede ver el listado de estudiantes."""
    if not user or not user.is_authenticated:
        return False
    # Staff puede ver todos, estudiantes solo se ven a sí mismos
    return is_staff(user) or is_practicante(user)


def can_view_companies(user) -> bool:
    """Verifica si el usuario puede ver el listado de empresas."""
    if not user or not user.is_authenticated:
        return False
    # Todos los autenticados pueden ver empresas
    return True


def can_view_supervisors(user) -> bool:
    """Verifica si el usuario puede ver el listado de supervisores."""
    if not user or not user.is_authenticated:
        return False
    # Todos los autenticados pueden ver supervisores
    return True


def can_view_practices(user) -> bool:
    """Verifica si el usuario puede ver el listado de prácticas."""
    if not user or not user.is_authenticated:
        return False
    # Todos los autenticados pueden ver prácticas (filtradas según rol)
    return True


def can_view_documents(user) -> bool:
    """Verifica si el usuario puede ver el listado de documentos."""
    if not user or not user.is_authenticated:
        return False
    # Todos los autenticados pueden ver documentos (filtrados según permisos)
    return True
