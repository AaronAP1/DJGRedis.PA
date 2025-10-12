"""
Sistema de logging de seguridad para detectar y registrar intentos de XSS.
"""

import logging
from typing import Optional, Dict, Any
from django.conf import settings
from django.utils import timezone


# Logger específico para eventos de seguridad
security_logger = logging.getLogger('security')


class SecurityEventLogger:
    """Clase para registrar eventos de seguridad."""
    
    @staticmethod
    def log_xss_attempt(
        original_content: str,
        sanitized_content: str,
        user_id: Optional[str] = None,
        field_name: Optional[str] = None,
        endpoint: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """
        Registra un intento potencial de XSS.
        
        Args:
            original_content: Contenido original antes de sanitizar
            sanitized_content: Contenido después de sanitizar
            user_id: ID del usuario que envió el contenido
            field_name: Nombre del campo afectado
            endpoint: Endpoint donde ocurrió el intento
            ip_address: Dirección IP del cliente
        """
        if not getattr(settings, 'XSS_LOG_ATTEMPTS', True):
            return
            
        # Solo registrar si hubo cambios (posible XSS)
        if original_content != sanitized_content:
            extra_data = {
                'event_type': 'xss_attempt',
                'user_id': user_id,
                'field_name': field_name,
                'endpoint': endpoint,
                'ip_address': ip_address,
                'original_length': len(original_content),
                'sanitized_length': len(sanitized_content),
                'original_preview': original_content[:200],  # Primeros 200 caracteres
                'timestamp': timezone.now().isoformat(),
                'severity': 'WARNING'
            }
            
            security_logger.warning(
                f"Potential XSS attempt detected - Field: {field_name or 'unknown'}, "
                f"User: {user_id or 'anonymous'}, Endpoint: {endpoint or 'unknown'}",
                extra=extra_data
            )
    
    @staticmethod
    def log_suspicious_input(
        content: str,
        reason: str,
        user_id: Optional[str] = None,
        field_name: Optional[str] = None,
        endpoint: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """
        Registra entrada sospechosa que no necesariamente es XSS.
        
        Args:
            content: Contenido sospechoso
            reason: Razón por la que es sospechoso
            user_id: ID del usuario
            field_name: Campo afectado
            endpoint: Endpoint donde ocurrió
            ip_address: IP del cliente
        """
        extra_data = {
            'event_type': 'suspicious_input',
            'user_id': user_id,
            'field_name': field_name,
            'endpoint': endpoint,
            'ip_address': ip_address,
            'content_length': len(content),
            'content_preview': content[:100],
            'reason': reason,
            'timestamp': timezone.now().isoformat(),
            'severity': 'INFO'
        }
        
        security_logger.info(
            f"Suspicious input detected - Reason: {reason}, "
            f"Field: {field_name or 'unknown'}, User: {user_id or 'anonymous'}",
            extra=extra_data
        )
    
    @staticmethod
    def log_security_event(
        event_type: str,
        message: str,
        user_id: Optional[str] = None,
        severity: str = 'INFO',
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """
        Registra un evento de seguridad genérico.
        
        Args:
            event_type: Tipo de evento (ej: 'file_upload', 'permission_denied')
            message: Mensaje descriptivo
            user_id: ID del usuario involucrado
            severity: Nivel de severidad (INFO, WARNING, ERROR, CRITICAL)
            extra_data: Datos adicionales del evento
        """
        log_data = {
            'event_type': event_type,
            'user_id': user_id,
            'timestamp': timezone.now().isoformat(),
            'severity': severity
        }
        
        if extra_data:
            log_data.update(extra_data)
        
        log_level = getattr(logging, severity.upper(), logging.INFO)
        security_logger.log(log_level, message, extra=log_data)


def get_client_ip(request) -> Optional[str]:
    """
    Obtiene la IP real del cliente considerando proxies.
    
    Args:
        request: Objeto request de Django
        
    Returns:
        Dirección IP del cliente
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_endpoint_info(request) -> str:
    """
    Obtiene información del endpoint actual.
    
    Args:
        request: Objeto request de Django
        
    Returns:
        String con información del endpoint
    """
    try:
        method = request.method
        path = request.path
        return f"{method} {path}"
    except Exception:
        return "unknown"


# Instancia global del logger
security_event_logger = SecurityEventLogger()
