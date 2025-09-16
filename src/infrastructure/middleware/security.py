"""
Custom security middleware to add extra security headers.
"""
from django.utils.deprecation import MiddlewareMixin


class SecurityMiddleware(MiddlewareMixin):
    """Add basic security headers (complements Django's default security middleware)."""

    def process_response(self, request, response):
        # Add Content Security Policy (adjust in production to your frontend domains)
        if not response.has_header("Content-Security-Policy"):
            response["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline';"

        # Additional headers
        response.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        return response
