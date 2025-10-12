"""
Decoradores para sanitización automática de datos de entrada.
"""

from functools import wraps
from typing import List, Dict, Any, Callable
from .sanitizers import validate_and_sanitize_input, sanitize_text_field, sanitize_rich_text
from .logging import get_client_ip, get_endpoint_info


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
