"""
Custom security middleware to add extra security headers.
"""
from django.utils.deprecation import MiddlewareMixin


class SecurityMiddleware(MiddlewareMixin):
    """Add basic security headers (complements Django's default security middleware)."""

    def process_response(self, request, response):
        # Add Content Security Policy (más restrictivo para mejor seguridad)
        if not response.has_header("Content-Security-Policy"):
            # CSP más estricto - ajustar según necesidades del frontend
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-eval'; "  # 'unsafe-eval' solo si es necesario para GraphQL/Apollo
                "style-src 'self' 'unsafe-inline'; "  # Permitir estilos inline temporalmente
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self' https:; "
                "media-src 'self'; "
                "object-src 'none'; "
                "frame-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
            response["Content-Security-Policy"] = csp_policy

        # Additional security headers
        response.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        response.setdefault("X-Content-Type-Options", "nosniff")
        response.setdefault("X-Frame-Options", "DENY")
        response.setdefault("X-XSS-Protection", "1; mode=block")
        
        return response
