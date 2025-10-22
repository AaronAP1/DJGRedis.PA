"""
Utilidades para sanitización de datos de entrada contra XSS.
"""

import bleach
from typing import Optional, List
from .logging import security_event_logger


# Tags HTML permitidos (muy restrictivo por defecto)
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
]

# Atributos permitidos por tag
ALLOWED_ATTRIBUTES = {
    '*': ['class'],
    'a': ['href', 'title'],
    'img': ['src', 'alt', 'width', 'height'],
}

# Protocolos permitidos en enlaces
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def sanitize_html(content: Optional[str], 
                  allowed_tags: Optional[List[str]] = None,
                  strip_tags: bool = False,
                  user_id: Optional[str] = None,
                  field_name: Optional[str] = None) -> str:
    """
    Sanitiza contenido HTML removiendo elementos peligrosos.
    
    Args:
        content: Contenido a sanitizar
        allowed_tags: Tags HTML permitidos (usa ALLOWED_TAGS por defecto)
        strip_tags: Si True, remueve todos los tags HTML
        user_id: ID del usuario para logging
        field_name: Nombre del campo para logging
    
    Returns:
        Contenido sanitizado
    """
    if not content:
        return ""
    
    original_content = content
    
    if strip_tags:
        # Remueve todos los tags HTML
        sanitized = bleach.clean(content, tags=[], strip=True)
    else:
        tags = allowed_tags or ALLOWED_TAGS
        sanitized = bleach.clean(
            content,
            tags=tags,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True
        )
    
    # Log si hubo cambios (posible XSS)
    if original_content != sanitized:
        security_event_logger.log_xss_attempt(
            original_content=original_content,
            sanitized_content=sanitized,
            user_id=user_id,
            field_name=field_name
        )
    
    return sanitized


def sanitize_text_field(content: Optional[str], 
                        user_id: Optional[str] = None,
                        field_name: Optional[str] = None) -> str:
    """
    Sanitiza campos de texto plano removiendo todo HTML.
    Ideal para nombres, títulos, descripciones cortas.
    """
    return sanitize_html(content, strip_tags=True, user_id=user_id, field_name=field_name)


def sanitize_rich_text(content: Optional[str],
                      user_id: Optional[str] = None,
                      field_name: Optional[str] = None) -> str:
    """
    Sanitiza contenido rico permitiendo tags básicos de formato.
    Ideal para descripciones largas, comentarios, etc.
    """
    return sanitize_html(content, allowed_tags=ALLOWED_TAGS, user_id=user_id, field_name=field_name)


def validate_and_sanitize_input(data: dict, 
                               text_fields: List[str] = None,
                               rich_text_fields: List[str] = None) -> dict:
    """
    Valida y sanitiza un diccionario de datos de entrada.
    
    Args:
        data: Diccionario con datos a sanitizar
        text_fields: Lista de campos que deben ser tratados como texto plano
        rich_text_fields: Lista de campos que permiten HTML básico
    
    Returns:
        Diccionario con datos sanitizados
    """
    text_fields = text_fields or []
    rich_text_fields = rich_text_fields or []
    
    sanitized_data = data.copy()
    
    for field in text_fields:
        if field in sanitized_data and sanitized_data[field]:
            sanitized_data[field] = sanitize_text_field(sanitized_data[field])
    
    for field in rich_text_fields:
        if field in sanitized_data and sanitized_data[field]:
            sanitized_data[field] = sanitize_rich_text(sanitized_data[field])
    
    return sanitized_data
