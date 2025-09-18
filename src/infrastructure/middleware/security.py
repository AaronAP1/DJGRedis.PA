"""
Custom security middleware to add extra security headers.
"""
from django.utils.deprecation import MiddlewareMixin


class SecurityMiddleware(MiddlewareMixin):
    """Add basic security headers (complements Django's default security middleware)."""

    def process_response(self, request, response):
        # Add Content Security Policy (relaxed for development)
        if not response.has_header("Content-Security-Policy"):
            # Relaxed CSP for development to allow Swagger/ReDoc CDN resources
            # Allow blob: for workers used by ReDoc/Swagger UI and permit
            # worker-src in development. Keep policy still reasonably restricted.
            csp_policy = (
                "default-src 'self'; "
                "img-src 'self' data: https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net blob:; "
                "worker-src 'self' blob:; "
                "font-src 'self' https://fonts.gstatic.com; "
                "connect-src 'self' https://api.github.com https://cdn.jsdelivr.net;"
            )
            response["Content-Security-Policy"] = csp_policy

        # Additional headers
        response.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        return response
