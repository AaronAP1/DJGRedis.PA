"""
Vistas de autenticación REST API con JWT.
Sistema completo de login/logout/refresh para usar con Postman.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, serializers
from rest_framework.request import Request
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model, authenticate
from django.conf import settings
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


# ============================================================================
# CUSTOM JWT SERIALIZER CON DATOS DE USUARIO
# ============================================================================

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado para incluir datos del usuario en la respuesta.
    Adaptado para trabajar con el campo 'correo' de la BD.
    """
    
    # Cambiar el campo que se usa para autenticación
    username_field = User.USERNAME_FIELD  # Esto es 'correo'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Permitir tanto 'email' como 'correo' en el input
        self.fields[self.username_field] = serializers.CharField(required=False)
        self.fields['email'] = serializers.CharField(required=False)
        self.fields['username'] = serializers.CharField(required=False)
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Agregar claims personalizados al token
        token['email'] = user.email  # Usa la property que traduce correo → email
        token['correo'] = user.correo  # Campo real de BD
        token['role'] = getattr(user.rol_id, 'nombre', 'PRACTICANTE') if user.rol_id else 'PRACTICANTE'
        token['full_name'] = user.get_full_name()
        token['user_id'] = str(user.id)
        
        return token
    
    def validate(self, attrs):
        # Normalizar campo de entrada (puede venir como 'email', 'username' o 'correo')
        email_value = attrs.get('email') or attrs.get('username') or attrs.get('correo') or attrs.get(self.username_field)
        
        if not email_value:
            raise serializers.ValidationError({
                'email': 'Se requiere email/correo para autenticación'
            })
        
        # Autenticar usando el backend personalizado
        from django.contrib.auth import authenticate
        
        password = attrs.get('password')
        if not password:
            raise serializers.ValidationError({
                'password': 'Se requiere contraseña'
            })
        
        # El backend EmailBackend espera 'username' pero busca por 'correo'
        user = authenticate(
            request=self.context.get('request'),
            username=email_value,  # EmailBackend lo buscará en campo 'correo'
            password=password
        )
        
        if user is None:
            raise serializers.ValidationError({
                'detail': 'Credenciales inválidas o usuario inactivo'
            })
        
        if not user.is_active:
            raise serializers.ValidationError({
                'detail': 'Usuario inactivo'
            })
        
        # Generar tokens
        refresh = self.get_token(user)
        
        # Guardar usuario para usarlo después
        self.user = user
        
        # Obtener el rol del usuario
        user_role = 'PRACTICANTE'
        if user.rol_id:
            user_role = user.rol_id.nombre
        
        # Construir respuesta
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
        # Agregar información del usuario a la respuesta
        data['user'] = {
            'id': user.id,
            'email': user.email,  # Property que traduce correo → email
            'correo': user.correo,  # Campo real de BD
            'username': user.email,
            'full_name': user.get_full_name(),
            'first_name': user.first_name,
            'last_name': user.last_name,
            'nombres': user.nombres,
            'apellidos': user.apellidos,
            'dni': user.dni,
            'role': user_role,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
        }
        
        # Log de seguridad
        logger.info(
            f"LOGIN_SUCCESS: User {user.email} (role={user_role}) authenticated via REST API"
        )
        
        return data


# ============================================================================
# LOGIN VIEW (POST /api/v1/auth/login/)
# ============================================================================

class LoginView(TokenObtainPairView):
    """
    Vista de Login REST con JWT.
    
    POST /api/v1/auth/login/
    Body:
    {
        "email": "user@upeu.edu.pe",
        "password": "password123"
    }
    
    O también con correo/username (compatibilidad):
    {
        "correo": "user@upeu.edu.pe",
        "password": "password123"
    }
    
    Response:
    {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "user": {
            "id": 1,
            "email": "user@upeu.edu.pe",
            "full_name": "John Doe",
            "role": "ADMINISTRADOR",
            "is_staff": true,
            "is_superuser": true
        }
    }
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        # Soporte para 'email', 'username' o 'correo'
        email = request.data.get('email') or request.data.get('username') or request.data.get('correo')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'success': False,
                'error': 'Se requieren email/correo y password'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear una copia mutable del request.data
        data = request.data.copy()
        # TokenObtainPairSerializer espera 'username' internamente
        # pero nuestro USERNAME_FIELD es 'correo'
        data['username'] = email
        
        # Crear un nuevo request con los datos modificados
        from rest_framework.request import Request
        from django.http import QueryDict
        
        # Modificar request.data
        request._full_data = data
        
        try:
            response = super().post(request, *args, **kwargs)
            
            # Agregar success flag
            if response.status_code == 200:
                response.data['success'] = True
                response.data['message'] = 'Login exitoso'
            
            return response
            
        except Exception as e:
            logger.warning(f"LOGIN_FAILED: {email} - {str(e)}")
            return Response({
                'success': False,
                'error': 'Credenciales inválidas o usuario inactivo'
            }, status=status.HTTP_401_UNAUTHORIZED)


# ============================================================================
# REFRESH TOKEN VIEW (POST /api/v1/auth/refresh/)
# ============================================================================

class RefreshTokenView(TokenRefreshView):
    """
    Vista para refrescar el access token.
    
    POST /api/v1/auth/refresh/
    Body:
    {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
    
    Response:
    {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
    """
    permission_classes = [permissions.AllowAny]


# ============================================================================
# LOGOUT VIEW (POST /api/v1/auth/logout/)
# ============================================================================

class LogoutView(APIView):
    """
    Vista de Logout REST.
    
    POST /api/v1/auth/logout/
    Headers:
        Authorization: Bearer <access_token>
    
    Body (opcional):
    {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
    
    Response:
    {
        "success": true,
        "message": "Logout exitoso"
    }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request):
        try:
            # Intentar blacklist del refresh token si se proporciona
            refresh_token = request.data.get('refresh')
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                    logger.info(f"LOGOUT_SUCCESS: Refresh token blacklisted")
                except Exception as e:
                    logger.warning(f"LOGOUT_WARNING: Could not blacklist token - {str(e)}")
            
            # Respuesta exitosa
            resp = Response({
                'success': True,
                'message': 'Logout exitoso'
            }, status=status.HTTP_200_OK)

            # Limpiar cookies si existen
            cookie_name = getattr(settings, 'GRAPHQL_JWT', {}).get('JWT_COOKIE_NAME', 'JWT')
            refresh_cookie_name = getattr(settings, 'GRAPHQL_JWT', {}).get('JWT_REFRESH_TOKEN_COOKIE_NAME', 'JWT_REFRESH_TOKEN')
            cookie_path = getattr(settings, 'GRAPHQL_JWT', {}).get('JWT_COOKIE_PATH', '/api/graphql/')
            resp.delete_cookie(cookie_name, path=cookie_path)
            resp.delete_cookie(refresh_cookie_name, path=cookie_path)
            
            return resp
            
        except Exception as e:
            logger.error(f"LOGOUT_ERROR: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error al cerrar sesión'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# ME VIEW (GET /api/v1/auth/me/)
# ============================================================================

class MeView(APIView):
    """
    Vista para obtener datos del usuario autenticado.
    
    GET /api/v1/auth/me/
    Headers:
        Authorization: Bearer <access_token>
    
    Response:
    {
        "id": 1,
        "email": "user@upeu.edu.pe",
        "full_name": "John Doe",
        "role": "ADMINISTRADOR",
        "is_staff": true,
        "is_superuser": true,
        "permissions": ["view_users", "create_practices", ...]
    }
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Obtener rol del usuario
        user_role = 'PRACTICANTE'
        if user.rol_id:
            user_role = user.rol_id.nombre
        
        # Obtener permisos
        permissions = []
        if hasattr(user, 'get_all_permissions'):
            try:
                permissions = user.get_all_permissions()
            except Exception as e:
                logger.warning(f"Could not get permissions for user {user.id}: {str(e)}")
        
        return Response({
            'id': user.id,
            'email': user.email,
            'correo': user.correo,
            'username': user.email,
            'full_name': user.get_full_name(),
            'first_name': user.first_name,
            'last_name': user.last_name,
            'nombres': user.nombres,
            'apellidos': user.apellidos,
            'dni': user.dni,
            'telefono': user.telefono,
            'role': user_role,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
            'permissions': list(permissions) if permissions else [],
            'last_login': user.last_login,
            'ultimo_acceso': user.ultimo_acceso,
        })
