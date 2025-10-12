"""
Middleware para autenticación JWT pura.
"""

from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import login
from django.conf import settings
from src.infrastructure.security.jwt_auth import JWTAuthenticationService


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware que maneja autenticación automática con JWT desde cookies.
    """
    
    def process_request(self, request):
        """
        Procesa la request para autenticar con JWT.
        """
        # Solo procesar si JWT está habilitado
        if not getattr(settings, 'JWT_AUTH_ENABLED', True):
            return None
        
        # No procesar si ya hay un usuario autenticado
        if hasattr(request, 'user') and request.user.is_authenticated:
            return None
        
        # Intentar autenticar con JWT
        user = JWTAuthenticationService.authenticate_request(request)
        
        if user:
            # Establecer usuario en la request
            request.user = user
            
            # También hacer login en Django para compatibilidad
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        return None


class JWTCookieMiddleware(MiddlewareMixin):
    """
    Middleware para manejar cookies JWT.
    """
    
    def process_response(self, request, response):
        """
        Procesa la respuesta para establecer o limpiar cookies JWT.
        """
        if not getattr(settings, 'JWT_AUTH_ENABLED', True):
            return response
        
        # Establecer cookies si se marcaron tokens
        if hasattr(request, '_jwt_access_token'):
            self._set_access_cookie(response, request._jwt_access_token)
        
        if hasattr(request, '_jwt_refresh_token'):
            self._set_refresh_cookie(response, request._jwt_refresh_token)
        
        # Limpiar cookies si se solicitó
        if hasattr(request, '_jwt_clear_cookies'):
            self._clear_jwt_cookies(response)
        
        return response
    
    def _set_access_cookie(self, response, token):
        """Establece cookie de access token."""
        # Usar configuración de SIMPLE_JWT
        simple_jwt = getattr(settings, 'SIMPLE_JWT', {})
        cookie_name = simple_jwt.get('AUTH_COOKIE', 'djgredis_session')
        
        # Calcular max_age desde ACCESS_TOKEN_LIFETIME
        access_lifetime = simple_jwt.get('ACCESS_TOKEN_LIFETIME')
        max_age = int(access_lifetime.total_seconds()) if access_lifetime else 900  # 15 min default
        
        print(f"🍪 ACCESS COOKIE CONFIG:")
        print(f"   Name: {cookie_name}")
        print(f"   Max Age: {max_age}")
        print(f"   Path: {simple_jwt.get('AUTH_COOKIE_PATH', '/')}")
        print(f"   Secure: {simple_jwt.get('AUTH_COOKIE_SECURE', not settings.DEBUG)}")
        print(f"   HttpOnly: {simple_jwt.get('AUTH_COOKIE_HTTP_ONLY', True)}")
        print(f"   SameSite: {simple_jwt.get('AUTH_COOKIE_SAMESITE', 'Lax' if settings.DEBUG else 'None')}")
        
        response.set_cookie(
            cookie_name,
            token,
            max_age=max_age,
            path=simple_jwt.get('AUTH_COOKIE_PATH', '/'),
            domain=simple_jwt.get('AUTH_COOKIE_DOMAIN'),
            secure=simple_jwt.get('AUTH_COOKIE_SECURE', not settings.DEBUG),
            httponly=simple_jwt.get('AUTH_COOKIE_HTTP_ONLY', True),
            samesite=simple_jwt.get('AUTH_COOKIE_SAMESITE', 'Lax' if settings.DEBUG else 'None')
        )
        
        print(f"✅ Cookie {cookie_name} establecida!")
    
    def _set_refresh_cookie(self, response, token):
        """Establece cookie de refresh token."""
        # Usar configuración de SIMPLE_JWT
        simple_jwt = getattr(settings, 'SIMPLE_JWT', {})
        cookie_name = simple_jwt.get('AUTH_COOKIE_REFRESH', 'djgredis_auth')
        
        # Calcular max_age desde REFRESH_TOKEN_LIFETIME
        refresh_lifetime = simple_jwt.get('REFRESH_TOKEN_LIFETIME')
        max_age = int(refresh_lifetime.total_seconds()) if refresh_lifetime else 432000  # 5 días default
        
        response.set_cookie(
            cookie_name,
            token,
            max_age=max_age,
            path=simple_jwt.get('AUTH_COOKIE_PATH', '/'),
            domain=simple_jwt.get('AUTH_COOKIE_DOMAIN'),
            secure=simple_jwt.get('AUTH_COOKIE_SECURE', not settings.DEBUG),
            httponly=simple_jwt.get('AUTH_COOKIE_HTTP_ONLY', True),
            samesite=simple_jwt.get('AUTH_COOKIE_SAMESITE', 'Lax' if settings.DEBUG else 'None')
        )
    
    def _clear_jwt_cookies(self, response):
        """Limpia todas las cookies JWT."""
        # Usar configuración de SIMPLE_JWT
        simple_jwt = getattr(settings, 'SIMPLE_JWT', {})
        
        # Limpiar access token
        access_cookie_name = simple_jwt.get('AUTH_COOKIE', 'djgredis_session')
        response.delete_cookie(
            access_cookie_name,
            path=simple_jwt.get('AUTH_COOKIE_PATH', '/'),
            domain=simple_jwt.get('AUTH_COOKIE_DOMAIN'),
            samesite=simple_jwt.get('AUTH_COOKIE_SAMESITE', 'Lax' if settings.DEBUG else 'None')
        )
        
        # Limpiar refresh token
        refresh_cookie_name = simple_jwt.get('AUTH_COOKIE_REFRESH', 'djgredis_auth')
        response.delete_cookie(
            refresh_cookie_name,
            path=simple_jwt.get('AUTH_COOKIE_PATH', '/'),
            domain=simple_jwt.get('AUTH_COOKIE_DOMAIN'),
            samesite=simple_jwt.get('AUTH_COOKIE_SAMESITE', 'Lax' if settings.DEBUG else 'None')
        )
        
        # También limpiar cookies comunes de Django
        response.delete_cookie(
            'sessionid',
            path='/',
            domain=None
        )
        
        # Limpiar CSRF token si existe
        response.delete_cookie(
            'csrftoken',
            path='/',
            domain=None
        )
