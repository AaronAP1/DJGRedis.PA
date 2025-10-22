"""
Middleware de seguridad para headers CSP, XSS y otros.
"""
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware para agregar headers de seguridad."""
    
    def process_response(self, request, response):
        # Content Security Policy
        if getattr(settings, 'CSP_ENABLED', True):
            csp_policy = self._build_csp_policy()
            if settings.DEBUG:
                response['Content-Security-Policy-Report-Only'] = csp_policy
            else:
                response['Content-Security-Policy'] = csp_policy
        
        # Headers adicionales de seguridad
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy (Feature Policy)
        permissions_policy = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=()"
        )
        response['Permissions-Policy'] = permissions_policy
        
        return response
    
    def _build_csp_policy(self):
        """Construye la política CSP basada en configuración."""
        # Política base restrictiva
        policy_parts = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://challenges.cloudflare.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self' https://challenges.cloudflare.com",
            "frame-src https://challenges.cloudflare.com",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        
        # En desarrollo, permitir localhost
        if settings.DEBUG:
            policy_parts.extend([
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' http://localhost:* https://challenges.cloudflare.com",
                "connect-src 'self' http://localhost:* ws://localhost:* https://challenges.cloudflare.com",
            ])
        
        return '; '.join(policy_parts)


class XSSProtectionMiddleware(MiddlewareMixin):
    """Middleware adicional para protección XSS."""
    
    def process_request(self, request):
        # Sanitizar parámetros GET que podrían contener XSS
        if request.GET:
            for key, value in request.GET.items():
                if self._contains_suspicious_content(value):
                    # Log del intento de XSS
                    import logging
                    logger = logging.getLogger('security')
                    logger.warning(f'Posible intento XSS detectado: {key}={value[:100]}')
        
        return None
    
    def _contains_suspicious_content(self, value):
        """Detecta contenido sospechoso de XSS."""
        suspicious_patterns = [
            '<script', '</script>', 'javascript:', 'onload=', 'onerror=',
            'onclick=', 'onmouseover=', 'onfocus=', 'onblur=', 'eval(',
            'alert(', 'confirm(', 'prompt('
        ]
        
        value_lower = value.lower()
        return any(pattern in value_lower for pattern in suspicious_patterns)
