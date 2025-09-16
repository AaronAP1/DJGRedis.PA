from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(BaseAuthentication):
    """
    DRF authentication class that reads the access JWT from an HttpOnly cookie
    and delegates validation to SimpleJWT's JWTAuthentication.

    - Cookie name is taken from settings.GRAPHQL_JWT['JWT_COOKIE_NAME'] (default: 'JWT').
    - If no cookie is present, returns None so other auth backends can try.
    - If the cookie is present but invalid/expired, raises AuthenticationFailed.
    """

    def __init__(self) -> None:
        self.jwt_auth = JWTAuthentication()

    def authenticate(self, request):
        jwt_settings = getattr(settings, 'GRAPHQL_JWT', {})
        cookie_name = jwt_settings.get('JWT_COOKIE_NAME', 'JWT')
        token = request.COOKIES.get(cookie_name)
        if not token:
            # No cookie -> let other authenticators run
            return None

        # Temporarily inject Authorization header for SimpleJWT
        old_auth = request.META.get('HTTP_AUTHORIZATION')
        try:
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'
            return self.jwt_auth.authenticate(request)
        except Exception:
            raise exceptions.AuthenticationFailed('Invalid JWT in cookie')
        finally:
            # Restore previous header state
            if old_auth is None:
                request.META.pop('HTTP_AUTHORIZATION', None)
            else:
                request.META['HTTP_AUTHORIZATION'] = old_auth

    def authenticate_header(self, request):
        return 'Bearer'
