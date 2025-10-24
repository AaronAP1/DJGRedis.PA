"""
Decoradores para sanitización automática de datos de entrada y control de permisos.
"""

from functools import wraps
from typing import List, Dict, Any, Callable
from graphql import GraphQLError
from .sanitizers import validate_and_sanitize_input, sanitize_text_field, sanitize_rich_text
from .logging import get_client_ip, get_endpoint_info
from .permission_helpers import is_staff, is_administrador, is_coordinador, is_secretaria


def sanitize_mutation_input(text_fields: List[str] = None, 
                           rich_text_fields: List[str] = None):
    """
    Decorador para sanitizar automáticamente inputs de mutaciones GraphQL.
    
    Args:
        text_fields: Lista de campos que deben ser tratados como texto plano
        rich_text_fields: Lista de campos que permiten HTML básico
    
    Usage:
        @sanitize_mutation_input(
            text_fields=['first_name', 'last_name', 'titulo'],
            rich_text_fields=['descripcion', 'mensaje']
        )
        def mutate(root, info, input):
            # input ya está sanitizado aquí
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Obtener contexto del usuario y request
            user_id = None
            request = None
            
            # En GraphQL, el contexto está en info.context
            if len(args) >= 2 and hasattr(args[1], 'context'):
                request = args[1].context
                if hasattr(request, 'user') and hasattr(request.user, 'id'):
                    user_id = str(request.user.id)
            
            # Buscar el parámetro 'input' en kwargs
            if 'input' in kwargs and hasattr(kwargs['input'], '__dict__'):
                input_data = kwargs['input'].__dict__.copy()
                
                # Sanitizar campos de texto plano
                for field in (text_fields or []):
                    if field in input_data and input_data[field]:
                        original = input_data[field]
                        sanitized = sanitize_text_field(
                            original, 
                            user_id=user_id, 
                            field_name=field
                        )
                        setattr(kwargs['input'], field, sanitized)
                
                # Sanitizar campos de texto rico
                for field in (rich_text_fields or []):
                    if field in input_data and input_data[field]:
                        original = input_data[field]
                        sanitized = sanitize_rich_text(
                            original, 
                            user_id=user_id, 
                            field_name=field
                        )
                        setattr(kwargs['input'], field, sanitized)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def sanitize_serializer_data(text_fields: List[str] = None,
                           rich_text_fields: List[str] = None):
    """
    Decorador para sanitizar datos en serializers de DRF.
    
    Usage:
        @sanitize_serializer_data(
            text_fields=['first_name', 'last_name'],
            rich_text_fields=['description']
        )
        def validate(self, data):
            # data ya está sanitizado aquí
            return data
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, data):
            # Sanitizar los datos antes de la validación
            sanitized_data = validate_and_sanitize_input(
                data,
                text_fields=text_fields or [],
                rich_text_fields=rich_text_fields or []
            )
            
            return func(self, sanitized_data)
        return wrapper
    return decorator


# ============================================================================
# DECORADORES DE PERMISOS PARA GRAPHQL
# ============================================================================

def staff_required(func: Callable) -> Callable:
    """
    Decorador que requiere que el usuario sea staff (Admin, Coordinador o Secretaria).
    
    Usage:
        @staff_required
        def mutate(root, info, ...):
            # Solo staff puede ejecutar esto
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # El segundo argumento es 'info' en GraphQL resolvers
        if len(args) >= 2 and hasattr(args[1], 'context'):
            info = args[1]
            user = info.context.user
            
            if not user or not user.is_authenticated:
                raise GraphQLError('Se requiere autenticación')
            
            if not is_staff(user):
                raise GraphQLError('Se requieren permisos de staff (Admin/Coordinador/Secretaria)')
            
            return func(*args, **kwargs)
        
        raise GraphQLError('Contexto inválido')
    return wrapper


def administrador_required(func: Callable) -> Callable:
    """
    Decorador que requiere que el usuario sea ADMINISTRADOR.
    
    Usage:
        @administrador_required
        def mutate(root, info, ...):
            # Solo administradores pueden ejecutar esto
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if len(args) >= 2 and hasattr(args[1], 'context'):
            info = args[1]
            user = info.context.user
            
            if not user or not user.is_authenticated:
                raise GraphQLError('Se requiere autenticación')
            
            if not is_administrador(user):
                raise GraphQLError('Se requieren permisos de ADMINISTRADOR')
            
            return func(*args, **kwargs)
        
        raise GraphQLError('Contexto inválido')
    return wrapper


def coordinador_required(func: Callable) -> Callable:
    """
    Decorador que requiere que el usuario sea COORDINADOR.
    
    Usage:
        @coordinador_required
        def mutate(root, info, ...):
            # Solo coordinadores pueden ejecutar esto
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if len(args) >= 2 and hasattr(args[1], 'context'):
            info = args[1]
            user = info.context.user
            
            if not user or not user.is_authenticated:
                raise GraphQLError('Se requiere autenticación')
            
            if not is_coordinador(user):
                raise GraphQLError('Se requieren permisos de COORDINADOR')
            
            return func(*args, **kwargs)
        
        raise GraphQLError('Contexto inválido')
    return wrapper


def secretaria_required(func: Callable) -> Callable:
    """
    Decorador que requiere que el usuario sea SECRETARIA.
    
    Usage:
        @secretaria_required
        def mutate(root, info, ...):
            # Solo secretarias pueden ejecutar esto
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if len(args) >= 2 and hasattr(args[1], 'context'):
            info = args[1]
            user = info.context.user
            
            if not user or not user.is_authenticated:
                raise GraphQLError('Se requiere autenticación')
            
            if not is_secretaria(user):
                raise GraphQLError('Se requieren permisos de SECRETARIA')
            
            return func(*args, **kwargs)
        
        raise GraphQLError('Contexto inválido')
    return wrapper


def role_required(*roles):
    """
    Decorador que requiere que el usuario tenga uno de los roles especificados.
    
    Usage:
        @role_required('COORDINADOR', 'ADMINISTRADOR')
        def mutate(root, info, ...):
            # Solo coordinadores o administradores pueden ejecutar esto
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if len(args) >= 2 and hasattr(args[1], 'context'):
                info = args[1]
                user = info.context.user
                
                if not user or not user.is_authenticated:
                    raise GraphQLError('Se requiere autenticación')
                
                if not hasattr(user, 'role') or user.role not in roles:
                    raise GraphQLError(f'Se requiere uno de estos roles: {", ".join(roles)}')
                
                return func(*args, **kwargs)
            
            raise GraphQLError('Contexto inválido')
        return wrapper
    return decorator
