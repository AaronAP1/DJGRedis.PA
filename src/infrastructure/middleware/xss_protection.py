"""
Middleware adicional para protección XSS avanzada.
"""

import re
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseBadRequest
from django.conf import settings
from src.infrastructure.security.logging import security_event_logger, get_client_ip


class XSSProtectionMiddleware(MiddlewareMixin):
    """
    Middleware para detectar y bloquear intentos de XSS en headers y parámetros.
    """
    
    # Patrones sospechosos en headers
    SUSPICIOUS_HEADER_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
        r'vbscript:',
        r'data:text/html',
    ]
    
    # Headers que deben ser validados
    HEADERS_TO_CHECK = [
        'HTTP_USER_AGENT',
        'HTTP_REFERER',
        'HTTP_X_FORWARDED_FOR',
        'HTTP_X_REAL_IP',
        'HTTP_ACCEPT',
        'HTTP_ACCEPT_LANGUAGE',
        'HTTP_ACCEPT_ENCODING',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL)
            for pattern in self.SUSPICIOUS_HEADER_PATTERNS
        ]
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Procesa la request para detectar contenido malicioso.
        """
        if not getattr(settings, 'XSS_PROTECTION_ENABLED', True):
            return None
        
        # Verificar headers sospechosos
        suspicious_headers = self._check_headers(request)
        if suspicious_headers:
            self._log_suspicious_activity(request, 'headers', suspicious_headers)
            # En desarrollo, solo logear. En producción, considerar bloquear.
            if not settings.DEBUG:
                return HttpResponseBadRequest("Request blocked due to security policy")
        
        # Verificar parámetros GET sospechosos
        suspicious_params = self._check_get_parameters(request)
        if suspicious_params:
            self._log_suspicious_activity(request, 'get_params', suspicious_params)
            if not settings.DEBUG:
                return HttpResponseBadRequest("Request blocked due to security policy")
        
        return None
    
    def _check_headers(self, request):
        """
        Verifica headers por contenido sospechoso.
        
        Returns:
            Dict con headers sospechosos encontrados
        """
        suspicious = {}
        
        for header_name in self.HEADERS_TO_CHECK:
            header_value = request.META.get(header_name, '')
            if header_value:
                for pattern in self.compiled_patterns:
                    if pattern.search(header_value):
                        suspicious[header_name] = header_value
                        break
        
        return suspicious
    
    def _check_get_parameters(self, request):
        """
        Verifica parámetros GET por contenido sospechoso.
        
        Returns:
            Dict con parámetros sospechosos encontrados
        """
        suspicious = {}
        
        for param_name, param_value in request.GET.items():
            if isinstance(param_value, str):
                for pattern in self.compiled_patterns:
                    if pattern.search(param_value):
                        suspicious[param_name] = param_value
                        break
        
        return suspicious
    
    def _log_suspicious_activity(self, request, activity_type, details):
        """
        Registra actividad sospechosa.
        
        Args:
            request: Objeto request de Django
            activity_type: Tipo de actividad ('headers', 'get_params')
            details: Detalles de la actividad sospechosa
        """
        user_id = None
        if hasattr(request, 'user') and hasattr(request.user, 'id'):
            user_id = str(request.user.id)
        
        security_event_logger.log_suspicious_input(
            content=str(details),
            reason=f"Suspicious {activity_type} detected",
            user_id=user_id,
            endpoint=f"{request.method} {request.path}",
            ip_address=get_client_ip(request)
        )


class ContentTypeValidationMiddleware(MiddlewareMixin):
    """
    Middleware para validar Content-Type en requests POST/PUT.
    """
    
    ALLOWED_CONTENT_TYPES = [
        'application/json',
        'application/x-www-form-urlencoded',
        'multipart/form-data',
        'text/plain',
    ]
    
    def process_request(self, request):
        """
        Valida Content-Type para requests que modifican datos.
        """
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.META.get('CONTENT_TYPE', '').split(';')[0].strip()
            
            # Permitir requests sin Content-Type (pueden ser válidos)
            if not content_type:
                return None
            
            # Verificar si el Content-Type está permitido
            if content_type not in self.ALLOWED_CONTENT_TYPES:
                # Log del intento sospechoso
                user_id = None
                if hasattr(request, 'user') and hasattr(request.user, 'id'):
                    user_id = str(request.user.id)
                
                security_event_logger.log_suspicious_input(
                    content=content_type,
                    reason="Unusual Content-Type header",
                    user_id=user_id,
                    field_name="Content-Type",
                    endpoint=f"{request.method} {request.path}",
                    ip_address=get_client_ip(request)
                )
                
                # En desarrollo solo logear, en producción considerar bloquear
                if not settings.DEBUG:
                    return HttpResponseBadRequest("Unsupported Content-Type")
        
        return None


class RateLimitByIPMiddleware(MiddlewareMixin):
    """
    Middleware simple para rate limiting por IP.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Implementa rate limiting básico por IP.
        """
        # Este es un ejemplo básico. En producción, usar django-ratelimit o similar
        from django.core.cache import cache
        
        ip = get_client_ip(request)
        if not ip:
            return None
        
        # Límite: 1000 requests por hora por IP
        cache_key = f"rate_limit:{ip}"
        current_requests = cache.get(cache_key, 0)
        
        if current_requests >= 1000:
            security_event_logger.log_security_event(
                event_type='rate_limit_exceeded',
                message=f"Rate limit exceeded for IP {ip}",
                severity='WARNING',
                extra_data={
                    'ip_address': ip,
                    'requests_count': current_requests,
                    'endpoint': f"{request.method} {request.path}"
                }
            )
            
            if not settings.DEBUG:
                return HttpResponseBadRequest("Rate limit exceeded")
        
        # Incrementar contador
        cache.set(cache_key, current_requests + 1, timeout=3600)  # 1 hora
        
        return None
