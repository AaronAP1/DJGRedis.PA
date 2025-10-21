"""
Decoradores para verificación de permisos en resolvers de GraphQL.

Estos decoradores simplifican la verificación de permisos en los
resolvers de GraphQL, manteniendo el código limpio y legible.
"""

from functools import wraps
from graphql import GraphQLError
from .permission_helpers import (
    is_administrador,
    is_coordinador,
    is_secretaria,
    is_supervisor,
    is_practicante,
    is_staff,
    has_any_role,
    require_authentication,
)


# ============================================================================
# DECORADORES BASE
# ============================================================================

def login_required(func):
    """
    Decorador que requiere que el usuario esté autenticado.
    
    Uso:
        @login_required
        def resolve_my_field(self, info):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        info = args[1] if len(args) > 1 else kwargs.get('info')
        user = info.context.user if info and hasattr(info, 'context') else None
        
        if not require_authentication(user):
            raise GraphQLError('Autenticación requerida')
        
        return func(*args, **kwargs)
    return wrapper


def role_required(*allowed_roles):
    """
    Decorador que requiere uno o más roles específicos.
    
    Uso:
        @role_required('ADMINISTRADOR', 'COORDINADOR')
        def resolve_admin_field(self, info):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            info = args[1] if len(args) > 1 else kwargs.get('info')
            user = info.context.user if info and hasattr(info, 'context') else None
            
            if not require_authentication(user):
                raise GraphQLError('Autenticación requerida')
            
            if not has_any_role(user, list(allowed_roles)):
                raise GraphQLError(
                    f'Permiso denegado. Se requiere uno de los siguientes roles: {", ".join(allowed_roles)}'
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# DECORADORES POR ROL ESPECÍFICO
# ============================================================================

def admin_required(func):
    """
    Decorador que requiere rol ADMINISTRADOR.
    
    Uso:
        @admin_required
        def resolve_admin_only_field(self, info):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        info = args[1] if len(args) > 1 else kwargs.get('info')
        user = info.context.user if info and hasattr(info, 'context') else None
        
        if not require_authentication(user):
            raise GraphQLError('Autenticación requerida')
        
        if not is_administrador(user):
            raise GraphQLError('Permiso denegado. Se requiere rol ADMINISTRADOR')
        
        return func(*args, **kwargs)
    return wrapper


def coordinator_required(func):
    """
    Decorador que requiere rol COORDINADOR.
    
    Uso:
        @coordinator_required
        def resolve_coordinator_field(self, info):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        info = args[1] if len(args) > 1 else kwargs.get('info')
        user = info.context.user if info and hasattr(info, 'context') else None
        
        if not require_authentication(user):
            raise GraphQLError('Autenticación requerida')
        
        if not is_coordinador(user):
            raise GraphQLError('Permiso denegado. Se requiere rol COORDINADOR')
        
        return func(*args, **kwargs)
    return wrapper


def staff_required(func):
    """
    Decorador que requiere personal administrativo (ADMIN, COORDINADOR, SECRETARIA).
    
    Uso:
        @staff_required
        def resolve_staff_field(self, info):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        info = args[1] if len(args) > 1 else kwargs.get('info')
        user = info.context.user if info and hasattr(info, 'context') else None
        
        if not require_authentication(user):
            raise GraphQLError('Autenticación requerida')
        
        if not is_staff(user):
            raise GraphQLError('Permiso denegado. Se requiere personal administrativo')
        
        return func(*args, **kwargs)
    return wrapper


def practicante_required(func):
    """
    Decorador que requiere rol PRACTICANTE.
    
    Uso:
        @practicante_required
        def resolve_student_field(self, info):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        info = args[1] if len(args) > 1 else kwargs.get('info')
        user = info.context.user if info and hasattr(info, 'context') else None
        
        if not require_authentication(user):
            raise GraphQLError('Autenticación requerida')
        
        if not is_practicante(user):
            raise GraphQLError('Permiso denegado. Se requiere rol PRACTICANTE')
        
        return func(*args, **kwargs)
    return wrapper


def supervisor_required(func):
    """
    Decorador que requiere rol SUPERVISOR.
    
    Uso:
        @supervisor_required
        def resolve_supervisor_field(self, info):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        info = args[1] if len(args) > 1 else kwargs.get('info')
        user = info.context.user if info and hasattr(info, 'context') else None
        
        if not require_authentication(user):
            raise GraphQLError('Autenticación requerida')
        
        if not is_supervisor(user):
            raise GraphQLError('Permiso denegado. Se requiere rol SUPERVISOR')
        
        return func(*args, **kwargs)
    return wrapper


# ============================================================================
# DECORADORES DE PROPIEDAD
# ============================================================================

def owner_or_staff_required(get_owner_func):
    """
    Decorador que requiere ser propietario del recurso o ser staff.
    
    Uso:
        @owner_or_staff_required(lambda obj: obj.user)
        def resolve_protected_field(self, info, id):
            obj = MyModel.objects.get(id=id)
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            info = args[1] if len(args) > 1 else kwargs.get('info')
            user = info.context.user if info and hasattr(info, 'context') else None
            
            if not require_authentication(user):
                raise GraphQLError('Autenticación requerida')
            
            # Ejecutar la función para obtener el objeto
            result = func(*args, **kwargs)
            
            # Si es staff, permitir acceso
            if is_staff(user):
                return result
            
            # Verificar propiedad
            if result:
                owner = get_owner_func(result)
                if owner != user:
                    raise GraphQLError('Permiso denegado. No eres el propietario de este recurso')
            
            return result
        return wrapper
    return decorator


# ============================================================================
# DECORADORES COMBINADOS
# ============================================================================

def admin_or_coordinator_required(func):
    """
    Decorador que requiere ADMINISTRADOR o COORDINADOR.
    
    Uso:
        @admin_or_coordinator_required
        def resolve_approval_field(self, info):
            ...
    """
    return role_required('ADMINISTRADOR', 'COORDINADOR')(func)


def admin_or_coordinator_or_secretary_required(func):
    """
    Decorador que requiere ADMINISTRADOR, COORDINADOR o SECRETARIA.
    
    Uso:
        @admin_or_coordinator_or_secretary_required
        def resolve_management_field(self, info):
            ...
    """
    return role_required('ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA')(func)


# ============================================================================
# UTILIDADES
# ============================================================================

def check_permission(info, permission_func, error_message=None):
    """
    Verifica un permiso personalizado y lanza un error si falla.
    
    Uso:
        check_permission(
            info,
            lambda user: can_view_practice(user, practice),
            "No tienes permiso para ver esta práctica"
        )
    """
    user = info.context.user if info and hasattr(info, 'context') else None
    
    if not require_authentication(user):
        raise GraphQLError('Autenticación requerida')
    
    if not permission_func(user):
        raise GraphQLError(error_message or 'Permiso denegado')


def get_user_from_info(info):
    """
    Extrae el usuario del contexto de info de GraphQL.
    
    Retorna:
        User object o None si no está autenticado
    """
    if info and hasattr(info, 'context'):
        return info.context.user
    return None


def verify_ownership(info, obj, owner_field='user'):
    """
    Verifica que el usuario sea propietario del objeto o sea staff.
    
    Args:
        info: GraphQL info object
        obj: Objeto a verificar
        owner_field: Nombre del campo que contiene el propietario
    
    Raises:
        GraphQLError si no tiene permiso
    """
    user = get_user_from_info(info)
    
    if not require_authentication(user):
        raise GraphQLError('Autenticación requerida')
    
    # Staff puede acceder a todo
    if is_staff(user):
        return
    
    # Verificar propiedad
    owner = getattr(obj, owner_field, None)
    if owner != user:
        raise GraphQLError('Permiso denegado. No eres el propietario de este recurso')
