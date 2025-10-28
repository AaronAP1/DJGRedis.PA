"""
Mutations GraphQL para autenticación JWT pura.
"""

import graphene
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from graphql import GraphQLError
from src.infrastructure.security.jwt_auth import JWTAuthenticationService
from src.infrastructure.security.logging import security_event_logger, get_client_ip

User = get_user_model()


class JWTLoginResponse(graphene.ObjectType):
    """Respuesta del login JWT."""
    success = graphene.Boolean(required=True)
    message = graphene.String(required=True)
    user = graphene.Field('src.adapters.primary.graphql_api.types.UserType')


class JWTRefreshResponse(graphene.ObjectType):
    """Respuesta del refresh JWT."""
    success = graphene.Boolean(required=True)
    message = graphene.String(required=True)


class JWTLogoutResponse(graphene.ObjectType):
    """Respuesta del logout JWT."""
    success = graphene.Boolean(required=True)
    message = graphene.String(required=True)


class JWTLogin(graphene.Mutation):
    """
    Mutation para login con JWT usando correo electrónico.
    Acepta 'correo' (email del usuario) como campo de autenticación.
    """
    
    class Arguments:
        correo = graphene.String(required=True, description="Email del usuario (correo electrónico)")
        password = graphene.String(required=True)
        cloudflare_token = graphene.String(required=False)
    
    Output = JWTLoginResponse
    
    def mutate(self, info, correo, password, cloudflare_token=None):
        request = info.context
        ip_address = get_client_ip(request)
        
        try:
            # Verificación Cloudflare Turnstile
            from src.infrastructure.security.cloudflare_turnstile import verify_turnstile_token
            from django.conf import settings
            
            if getattr(settings, 'CLOUDFLARE_TURNSTILE_ENABLED', False):
                if not verify_turnstile_token(cloudflare_token, ip_address):
                    raise GraphQLError(
                        "Verificación de seguridad fallida",
                        extensions={
                            'code': 'TURNSTILE_FAILED',
                            'field': 'cloudflare_token'
                        }
                    )
            
            # Validar credenciales (authenticate usa 'username' como parámetro pero busca por correo)
            user = authenticate(request=request, username=correo, password=password)
            if not user:
                # Log intento fallido
                security_event_logger.log_security_event(
                    'login_failed',
                    f"Failed login attempt for correo: {correo}",
                    extra_data={
                        'correo': correo,
                        'ip_address': ip_address,
                        'reason': 'invalid_credentials'
                    },
                    severity='WARNING'
                )
                
                raise GraphQLError(
                    "Credenciales inválidas",
                    extensions={
                        'code': 'INVALID_CREDENTIALS',
                        'field': 'correo'
                    }
                )
            
            if not user.is_active:
                security_event_logger.log_security_event(
                    'login_failed',
                    f"Login attempt for inactive user: {correo}",
                    user_id=str(user.id),
                    extra_data={
                        'correo': correo,
                        'ip_address': ip_address,
                        'reason': 'inactive_user'
                    },
                    severity='WARNING'
                )
                
                raise GraphQLError(
                    "Usuario inactivo",
                    extensions={
                        'code': 'USER_INACTIVE',
                        'field': 'correo'
                    }
                )
            
            # Crear sesión JWT
            access_token, refresh_token, response_data = JWTAuthenticationService.create_jwt_session(
                user, request
            )
            
            # Marcar tokens para cookies
            setattr(request, '_jwt_access_token', access_token)
            setattr(request, '_jwt_refresh_token', refresh_token)
            
            return JWTLoginResponse(
                success=response_data['success'],
                message=response_data['message'],
                user=user
            )
            
        except GraphQLError:
            raise
        except Exception as e:
            # Log del error completo
            import traceback
            error_traceback = traceback.format_exc()
            
            security_event_logger.log_security_event(
                'login_error',
                f"Login error for correo {correo}: {str(e)}",
                extra_data={
                    'correo': correo,
                    'ip_address': ip_address,
                    'error': str(e),
                    'traceback': error_traceback
                },
                severity='ERROR'
            )
            
            # En desarrollo, mostrar el error real
            from django.conf import settings
            if settings.DEBUG:
                raise GraphQLError(
                    f"Error interno: {str(e)}",
                    extensions={
                        'code': 'INTERNAL_ERROR',
                        'debug_message': str(e),
                        'traceback': error_traceback
                    }
                )
            else:
                raise GraphQLError(
                    "Error interno del servidor",
                    extensions={
                        'code': 'INTERNAL_ERROR'
                    }
                )


class JWTRefresh(graphene.Mutation):
    """
    Mutation para refresh de tokens JWT.
    """
    
    Output = JWTRefreshResponse
    
    def mutate(self, info):
        request = info.context
        
        try:
            # Refrescar tokens
            new_access_token, new_refresh_token, success = JWTAuthenticationService.refresh_jwt_tokens(request)
            
            if not success:
                raise GraphQLError(
                    "Token de refresh inválido o expirado",
                    extensions={
                        'code': 'INVALID_REFRESH_TOKEN'
                    }
                )
            
            # Marcar nuevos tokens para cookies
            setattr(request, '_jwt_access_token', new_access_token)
            if new_refresh_token:
                setattr(request, '_jwt_refresh_token', new_refresh_token)
            
            return JWTRefreshResponse(
                success=True,
                message="Tokens refrescados exitosamente"
            )
            
        except GraphQLError:
            raise
        except Exception as e:
            security_event_logger.log_security_event(
                'refresh_error',
                f"Token refresh error: {str(e)}",
                severity='ERROR'
            )
            
            raise GraphQLError(
                "Error refrescando tokens",
                extensions={
                    'code': 'REFRESH_ERROR'
                }
            )


class JWTLogout(graphene.Mutation):
    """
    Mutation para logout JWT con blacklist.
    """
    
    class Arguments:
        logout_all = graphene.Boolean(default_value=False)
    
    Output = JWTLogoutResponse
    
    def mutate(self, info, logout_all=False):
        request = info.context
        
        try:
            # Cerrar sesión JWT
            success, message = JWTAuthenticationService.logout_jwt_session(request, logout_all)
            
            if not success:
                return JWTLogoutResponse(
                    success=False,
                    message=message
                )
            
            # Marcar para limpiar cookies
            setattr(request, '_jwt_clear_cookies', True)
            
            return JWTLogoutResponse(
                success=True,
                message=message
            )
            
        except Exception as e:
            security_event_logger.log_security_event(
                'logout_error',
                f"Logout error: {str(e)}",
                severity='ERROR'
            )
            
            return JWTLogoutResponse(
                success=False,
                message="Error al cerrar sesión"
            )


class JWTSessionStatus(graphene.ObjectType):
    """Estado de la sesión JWT."""
    is_authenticated = graphene.Boolean(required=True)
    user = graphene.Field('src.adapters.primary.graphql_api.types.UserType')
    expires_in = graphene.Int()  # Segundos hasta expiración


class JWTGetSessionStatus(graphene.ObjectType):
    """Query para obtener estado de sesión JWT."""
    
    jwt_session_status = graphene.Field(JWTSessionStatus)
    
    def resolve_jwt_session_status(self, info):
        """Resuelve el estado de la sesión JWT."""
        request = info.context
        
        # Verificar si hay usuario autenticado
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return JWTSessionStatus(
                is_authenticated=False,
                user=None,
                expires_in=None
            )
        
        # Calcular tiempo de expiración del access token
        access_token = JWTAuthenticationService._extract_access_token(request)
        expires_in = None
        
        if access_token:
            try:
                from rest_framework_simplejwt.tokens import AccessToken
                token = AccessToken(access_token)
                import time
                expires_in = int(token['exp'] - time.time())
                if expires_in < 0:
                    expires_in = 0
            except:
                expires_in = 0
        
        return JWTSessionStatus(
            is_authenticated=True,
            user=request.user,
            expires_in=expires_in
        )
