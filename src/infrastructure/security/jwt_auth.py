"""
Sistema de autenticación JWT PURO.
"""

from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from .logging import security_event_logger, get_client_ip

User = get_user_model()


class JWTAuthenticationService:
    """
    Servicio de autenticación JWT puro.
    
    Maneja:
    - Login con cookies JWT
    - Refresh de tokens
    - Logout con blacklist
    - Validación de tokens
    """
    
    def authenticate_request(request):
        """
        Autentica una request usando JWT desde cookies.
        
        Args:
            request: Request de Django
            
        Returns:
            User: Usuario autenticado o None
        """
        access_token = JWTAuthenticationService._get_token_from_cookies(
            request, 'access'
        )
        
        if not access_token:
            return None
        
        try:
            # Validar y decodificar token
            validated_token = AccessToken(access_token)
            user_id = validated_token['user_id']
            
            # Obtener usuario
            user = User.objects.get(id=user_id)
            
            if not user.is_active:
                return None
            
            # Actualizar ultimo_acceso si está configurado
            if getattr(settings, 'JWT_UPDATE_LAST_LOGIN', True):
                user.ultimo_acceso = timezone.now()
                user.save(update_fields=['ultimo_acceso'])
            
            return user
            
        except (TokenError, InvalidToken) as e:
            return None
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def _get_token_from_cookies(request, token_type):
        """
        Obtiene token JWT desde cookies usando configuración SIMPLE_JWT.
        
        Args:
            request: Request de Django
            token_type: 'access' o 'refresh'
            
        Returns:
            str: Token o None
        """
        simple_jwt = getattr(settings, 'SIMPLE_JWT', {})
        
        if token_type == 'access':
            cookie_name = simple_jwt.get('AUTH_COOKIE', 'djgredis_session')
        elif token_type == 'refresh':
            cookie_name = simple_jwt.get('AUTH_COOKIE_REFRESH', 'djgredis_auth')
        else:
            return None
        
        token = request.COOKIES.get(cookie_name)
        return token
    
    @staticmethod
    def _extract_access_token(request):
        """
        Extrae el access token de las cookies.
        
        Args:
            request: Request de Django
            
        Returns:
            str: Access token o None
        """
        if not hasattr(request, 'COOKIES'):
            return None
        
        cookie_name = getattr(settings, 'ACCESS_COOKIE_NAME', 'access_token')
        return request.COOKIES.get(cookie_name)
    
    @staticmethod
    def _extract_refresh_token(request):
        """
        Extrae el refresh token de las cookies.
        
        Args:
            request: Request de Django
            
        Returns:
            str: Refresh token o None
        """
        if not hasattr(request, 'COOKIES'):
            return None
        
        cookie_name = getattr(settings, 'REFRESH_COOKIE_NAME', 'refresh_token')
        return request.COOKIES.get(cookie_name)
    
    @staticmethod
    def create_jwt_session(user, request=None):
        """
        Crea una nueva sesión JWT con cookies.
        
        Args:
            user: Usuario
            request: Request de Django
            
        Returns:
            tuple: (access_token, refresh_token, response_data)
        """
        ip_address = get_client_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
        
        # Crear JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Crear OutstandingToken para tracking
        try:
            outstanding_token, created = OutstandingToken.objects.get_or_create(
                jti=refresh['jti'],
                defaults={
                    'user': user,
                    'token': str(refresh),
                    'expires_at': timezone.datetime.fromtimestamp(refresh['exp'])
                }
            )
        except Exception:
            pass  # Continuar sin OutstandingToken si falla
        
        # Actualizar ultimo_acceso (last_login es un property que apunta a este campo)
        user.ultimo_acceso = timezone.now()
        user.save(update_fields=['ultimo_acceso'])
        
        # Log de seguridad
        security_event_logger.log_security_event(
            'jwt_session_created',
            f"New JWT session created for user {user.email}",
            user_id=str(user.id),
            extra_data={
                'jwt_id': refresh['jti'],
                'ip_address': ip_address,
                'user_agent': user_agent[:100]
            }
        )
        
        response_data = {
            'success': True,
            'message': 'Login exitoso',
            'user': {
                'id': str(user.id),
                'email': user.correo,  # Campo real: correo
                'correo': user.correo,
                'nombres': user.nombres,  # Campo real: nombres
                'apellidos': user.apellidos,  # Campo real: apellidos
                'nombreCompleto': f"{user.nombres} {user.apellidos}".strip(),
                'lastLogin': user.ultimo_acceso.isoformat() if user.ultimo_acceso else None,
            }
        }
        
        return str(access_token), str(refresh), response_data
    
    @staticmethod
    def refresh_jwt_tokens(request):
        """
        Refresca los JWT tokens usando el refresh token.
        
        Args:
            request: Request de Django
            
        Returns:
            tuple: (new_access_token, new_refresh_token, success)
        """
        refresh_token = JWTAuthenticationService._get_token_from_cookies(request, 'refresh')
        if not refresh_token:
            return None, None, False
        
        try:
            # Validar refresh token
            refresh = RefreshToken(refresh_token)
            
            # Verificar que no esté en blacklist
            try:
                outstanding_token = OutstandingToken.objects.get(jti=refresh['jti'])
                if hasattr(outstanding_token, 'blacklistedtoken'):
                    return None, None, False
            except OutstandingToken.DoesNotExist:
                pass
            
            # Crear nuevo access token
            new_access_token = refresh.access_token
            
            # Opcionalmente rotar refresh token
            rotate_tokens = getattr(settings, 'SIMPLE_JWT', {}).get('ROTATE_REFRESH_TOKENS', False)
            if rotate_tokens:
                refresh.blacklist()
                new_refresh = RefreshToken.for_user(refresh.user)
                new_refresh_token = str(new_refresh)
            else:
                new_refresh_token = str(refresh)
            
            return str(new_access_token), new_refresh_token, True
            
        except (TokenError, InvalidToken) as e:
            return None, None, False
    
    @staticmethod
    def logout_jwt_session(request, logout_all=False):
        """
        Cierra sesión JWT agregando tokens a blacklist.
        
        Args:
            request: Request de Django
            logout_all: Si cerrar todas las sesiones del usuario
            
        Returns:
            tuple: (success, message)
        """
        refresh_token = JWTAuthenticationService._get_token_from_cookies(request, 'refresh')
        if not refresh_token:
            return False, "No hay sesión activa"
        
        try:
            refresh = RefreshToken(refresh_token)
            user_id = refresh.get('user_id')
            
            if logout_all and user_id:
                # Cerrar todas las sesiones del usuario
                user = User.objects.get(id=user_id)
                count = JWTAuthenticationService._blacklist_all_user_tokens(user)
                message = f"Se cerraron {count} sesiones"
            else:
                # Cerrar solo la sesión actual
                refresh.blacklist()
                message = "Sesión cerrada exitosamente"
            
            # Log de seguridad
            security_event_logger.log_security_event(
                'jwt_session_logout',
                f"JWT session logout for user_id {user_id}",
                user_id=str(user_id) if user_id else None,
                extra_data={
                    'jwt_id': refresh['jti'],
                    'logout_all': logout_all
                }
            )
            
            return True, message
            
        except (TokenError, InvalidToken, User.DoesNotExist) as e:
            return False, "Sesión inválida"
    
    @staticmethod
    def _blacklist_all_user_tokens(user):
        """
        Agrega todos los tokens activos de un usuario a la blacklist.
        
        Args:
            user: Usuario
            
        Returns:
            int: Número de tokens agregados a blacklist
        """
        outstanding_tokens = OutstandingToken.objects.filter(user=user)
        count = 0
        
        for token in outstanding_tokens:
            # Verificar que no esté ya en blacklist
            if not hasattr(token, 'blacklistedtoken'):
                BlacklistedToken.objects.get_or_create(token=token)
                count += 1
        
        return count
    
    @staticmethod
    def get_user_from_token(token_string):
        """
        Obtiene el usuario desde un token JWT.
        
        Args:
            token_string: Token JWT como string
            
        Returns:
            User o None
        """
        try:
            token = AccessToken(token_string)
            user_id = token.get('user_id')
            return User.objects.get(id=user_id, is_active=True)
        except (TokenError, InvalidToken, User.DoesNotExist):
            return None
