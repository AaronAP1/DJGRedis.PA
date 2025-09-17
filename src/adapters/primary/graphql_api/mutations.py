"""
Mutations GraphQL para el sistema de gestión de prácticas profesionales.
"""

import graphene
import graphql_jwt
try:
    from graphql_jwt.decorators import login_required, allow_any  # type: ignore
except Exception:  # pragma: no cover
    # Algunas versiones de graphql_jwt no exponen allow_any; definimos un no-op.
    from graphql_jwt.decorators import login_required  # type: ignore

    def allow_any(func):  # nosec - decorador no-op para permitir acceso anónimo
        return func
from django.contrib.auth import get_user_model
from graphql_relay import from_global_id
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.core.files.base import ContentFile
import secrets
import logging
import base64
import imghdr
import time
import requests
from urllib.parse import urlparse
from rest_framework_simplejwt.tokens import RefreshToken as DRFRefreshToken

from .types import (
    UserType, StudentType, CompanyType, SupervisorType,
    PracticeType, DocumentType, NotificationType,
    UserInput, UserUpdateInput, ProfileInput, StudentInput, CompanyInput,
    PracticeInput
)
from src.adapters.secondary.database.models import (
    Student, Company, Supervisor, Practice, Document, Notification
)
from src.domain.enums import UserRole, PracticeStatus, CompanyStatus
from src.infrastructure.security.recaptcha import verify_recaptcha
try:
    from graphql_jwt.refresh_token.models import RefreshToken as GQLRefreshToken
except Exception:  # pragma: no cover
    GQLRefreshToken = None

User = get_user_model()


# Utilidad: normaliza un ID aceptando tanto Global ID (Relay) como UUID crudo
def _resolve_real_id(raw_id: str) -> str:
    """Devuelve el UUID real desde un Global ID o el propio valor si ya es UUID.
    Limpia espacios y comillas tipográficas que a veces llegan desde el navegador.
    """
    try:
        s = str(raw_id or '').strip()
    except Exception:
        s = ''
    if not s:
        return ''
    # Eliminar comillas tipográficas u otros delimitadores extraños
    for ch in ('\u201c', '\u201d', '\u00ab', '\u00bb', '“', '”', '«', '»'):
        s = s.replace(ch, '')
    s = s.strip()
    if not s:
        return ''
    # Intentar decodificar como Global ID (Relay)
    try:
        _type, decoded = from_global_id(s)
        if decoded:
            return decoded
    except Exception:
        pass
    return s

# ===== MUTATIONS PARA USUARIOS =====
class CreateUser(graphene.Mutation):
    """Mutation para crear un usuario."""
    
    class Arguments:
        input = UserInput(required=True)
    
    success = graphene.Boolean()
    user = graphene.Field(UserType)
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, input):
        user = info.context.user
        if user.role != 'ADMINISTRADOR':
            return CreateUser(success=False, message="Solo ADMINISTRADOR puede crear usuarios")
        
        try:
            with transaction.atomic():
                # Validar dominio de email permitido
                try:
                    domain = input.email.split('@')[1].lower()
                except Exception:
                    domain = ''
                allowed = [d.lower() for d in getattr(settings, 'ALLOWED_EMAIL_DOMAINS', [])]
                if allowed and domain not in allowed:
                    return CreateUser(success=False, message='Dominio de email no permitido')

                # Validar duplicados (email, username)
                if User.objects.filter(email__iexact=input.email).exists():
                    return CreateUser(success=False, message='Email ya registrado')
                if getattr(input, 'username', None):
                    if User.objects.filter(username__iexact=input.username).exists():
                        return CreateUser(success=False, message='Usuario (username) ya registrado')

                new_user = User.objects.create_user(
                    email=input.email,
                    password=input.password,
                    first_name=input.first_name,
                    last_name=input.last_name,
                    role=input.role,
                    is_active=(True if input.is_active is None else bool(input.is_active)),
                    username=getattr(input, 'username', None) or None,
                )

                # Si es PRACTICANTE, exigir y crear Student con código
                if new_user.role == 'PRACTICANTE':
                    codigo = (getattr(input, 'codigo_estudiante', '') or '').strip()
                    if not codigo:
                        return CreateUser(success=False, message='codigo_estudiante es obligatorio para PRACTICANTE')
                    # Si no se proporcionó password, usar el código como contraseña
                    if not input.password:
                        new_user.set_password(codigo)
                        new_user.save(update_fields=['password'])
                    Student.objects.create(
                        user=new_user,
                        codigo_estudiante=codigo,
                    )
                # Enviar correo de bienvenida (solo si está habilitado)
                if getattr(settings, 'EMAIL_ENABLED', False):
                    try:
                        ctx = { 'user': new_user }
                        html_body = render_to_string('emails/user_welcome.html', ctx)
                        msg = EmailMultiAlternatives(
                            'Cuenta creada exitosamente',
                            html_body,
                            settings.DEFAULT_FROM_EMAIL,
                            [new_user.email]
                        )
                        msg.attach_alternative(html_body, 'text/html')
                        msg.send()
                    except Exception:
                        pass
                
                return CreateUser(
                    success=True,
                    user=new_user,
                    message="Usuario creado exitosamente"
                )
        except Exception as e:
            return CreateUser(success=False, message=f"Error al crear usuario: {str(e)}")


class UpdateUser(graphene.Mutation):
    """Mutation para actualizar un usuario."""
    
    class Arguments:
        id = graphene.ID(required=True)
        input = UserUpdateInput(required=True)
    
    success = graphene.Boolean()
    user = graphene.Field(UserType)
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, id, input):
        user = info.context.user
        if user.role != 'ADMINISTRADOR':
            return UpdateUser(success=False, message="Solo ADMINISTRADOR puede actualizar usuarios")
        
        try:
            real_id = _resolve_real_id(id)
            if not real_id:
                return UpdateUser(success=False, message="ID inválido")
            target_user = User.objects.get(id=real_id)
            
            # Actualizar campos
            if input.email:
                try:
                    domain = input.email.split('@')[1].lower()
                except Exception:
                    domain = ''
                allowed = [d.lower() for d in getattr(settings, 'ALLOWED_EMAIL_DOMAINS', [])]
                if allowed and domain not in allowed:
                    return UpdateUser(success=False, message='Dominio de email no permitido')
                if User.objects.filter(email__iexact=input.email).exclude(id=target_user.id).exists():
                    return UpdateUser(success=False, message='Email ya registrado')
                target_user.email = input.email
            if input.first_name:
                target_user.first_name = input.first_name
            if input.last_name:
                target_user.last_name = input.last_name
            if input.role:
                target_user.role = input.role
            if input.password:
                target_user.set_password(input.password)
            if getattr(input, 'username', None):
                if User.objects.filter(username__iexact=input.username).exclude(id=target_user.id).exists():
                    return UpdateUser(success=False, message='Usuario (username) ya registrado')
                target_user.username = input.username
            if input.is_active is not None:
                target_user.is_active = bool(input.is_active)
            
            target_user.save()
            
            return UpdateUser(
                success=True,
                user=target_user,
                message="Usuario actualizado exitosamente"
            )
        except User.DoesNotExist:
            return UpdateUser(success=False, message="Usuario no encontrado")
        except Exception as e:
            return UpdateUser(success=False, message=f"Error al actualizar usuario: {str(e)}")


class UpdateMyProfile(graphene.Mutation):
    """Actualiza el perfil del usuario autenticado (nombres, apellidos, username)."""

    class Arguments:
        input = ProfileInput(required=True)

    success = graphene.Boolean()
    user = graphene.Field(UserType)
    message = graphene.String()

    @staticmethod
    @login_required
    def mutate(root, info, input):
        user = info.context.user
        try:
            changed = False
            # Username
            new_username = getattr(input, 'username', None)
            if new_username:
                val = (new_username or '').strip()
                if val and val.lower() != (user.username or '').lower():
                    if User.objects.filter(username__iexact=val).exclude(id=user.id).exists():
                        return UpdateMyProfile(success=False, message='Usuario (username) ya registrado')
                    user.username = val
                    changed = True
            # First name / Last name
            if getattr(input, 'first_name', None):
                user.first_name = (input.first_name or '').strip()
                changed = True
            if getattr(input, 'last_name', None):
                user.last_name = (input.last_name or '').strip()
                changed = True

            if changed:
                user.save(update_fields=['username','first_name','last_name','updated_at'])
                return UpdateMyProfile(success=True, user=user, message='Perfil actualizado')
            else:
                return UpdateMyProfile(success=True, user=user, message='Sin cambios')
        except Exception as e:
            return UpdateMyProfile(success=False, message=f'Error al actualizar perfil: {str(e)}')


# ===== AUTH MUTATIONS (LOGIN / PASSWORD RESET) =====
class TokenAuth(graphene.Mutation):
    """Mutation de login con verificación de reCAPTCHA y dominio permitido."""

    class Arguments:
        # Permitir login con username o email (preferencia: username)
        username = graphene.String(required=False)
        email = graphene.String(required=False)
        password = graphene.String(required=True)
        recaptcha_token = graphene.String(required=True)

    success = graphene.Boolean()
    token = graphene.String()
    refresh_token = graphene.String()
    user = graphene.Field(UserType)
    message = graphene.String()

    @staticmethod
    @allow_any
    def mutate(root, info, password, username=None, email=None, recaptcha_token=None):
        request = info.context

        # reCAPTCHA
        if getattr(settings, 'RECAPTCHA_ENABLED', False):
            if not verify_recaptcha(recaptcha_token, request.META.get('REMOTE_ADDR')):
                return TokenAuth(success=False, message='reCAPTCHA inválido')

        # Intentos por identificador (email o username) - 30 en 1h
        ident = (username or email or '').lower()
        key_attempts = f"loginfail:{ident}"
        key_notify = f"loginfailnotify:{ident}"
        blocked = cache.get(key_attempts)
        if isinstance(blocked, int) and blocked >= 30:
            # Intentar enviar notificación de bloqueo una sola vez por ventana
            try:
                if cache.add(key_notify, 1, timeout=3600):
                    # Resolver email destinatario
                    recipient = None
                    if email:
                        recipient = email
                    elif username:
                        try:
                            recipient = User.objects.filter(username__iexact=username).values_list('email', flat=True).first()
                        except Exception:
                            recipient = None
                    if recipient and getattr(settings, 'EMAIL_ENABLED', False):
                        ctx = { 'email': recipient }
                        html_body = render_to_string('emails/account_locked.html', ctx)
                        msg = EmailMultiAlternatives(
                            'Cuenta bloqueada temporalmente',
                            html_body,
                            settings.DEFAULT_FROM_EMAIL,
                            [recipient]
                        )
                        msg.attach_alternative(html_body, 'text/html')
                        msg.send()
                        # Además, generar OTP y enviar email de "olvidaste tu contraseña" con el mismo diseño
                        try:
                            # Intentar obtener usuario real para el saludo; si no existe, continuar sin él
                            user_obj = None
                            try:
                                user_obj = User.objects.filter(email__iexact=recipient).first()
                            except Exception:
                                user_obj = None
                            otp_code = str(secrets.randbelow(1000000)).zfill(6)
                            cache.set(f"pwdotp:{recipient.lower()}", otp_code, timeout=600)
                            ctx2 = { 'user': user_obj, 'code': otp_code }
                            html2 = render_to_string('emails/password_reset_code.html', ctx2)
                            msg2 = EmailMultiAlternatives('Código para restablecer contraseña', html2, settings.DEFAULT_FROM_EMAIL, [recipient])
                            msg2.attach_alternative(html2, 'text/html')
                            msg2.send()
                        except Exception:
                            pass
            except Exception:
                pass
            try:
                logging.getLogger('security').warning('Cuenta bloqueada por intentos fallidos: %s', (email or username or ''))
            except Exception:
                pass
            return TokenAuth(success=False, message='Usuario temporalmente bloqueado por múltiples intentos fallidos (1 hora)')

        # Dominio permitido (solo si usa email para login)
        if email:
            try:
                domain = email.split('@')[1].lower()
            except Exception:
                domain = ''
            allowed = [d.lower() for d in getattr(settings, 'ALLOWED_EMAIL_DOMAINS', [])]
            if allowed and domain not in allowed:
                return TokenAuth(success=False, message='Dominio de email no permitido')

        # Autenticación estricta por credenciales (ignorar cualquier JWT en cookies/headers)
        try:
            if username:
                target_user = User.objects.get(username__iexact=username)
            else:
                target_user = User.objects.get(email__iexact=(email or ''))
        except User.DoesNotExist:
            try:
                created = cache.add(key_attempts, 1, timeout=3600)
                if not created:
                    new_val = cache.incr(key_attempts)
                    # Si alcanzó umbral, enviar aviso (una vez)
                    if isinstance(new_val, int) and new_val >= 30:
                        try:
                            if cache.add(key_notify, 1, timeout=3600):
                                # Si tenemos email en el intento, notificar
                                if email and getattr(settings, 'EMAIL_ENABLED', False):
                                    ctx = { 'email': email }
                                    html_body = render_to_string('emails/account_locked.html', ctx)
                                    msg = EmailMultiAlternatives('Cuenta bloqueada temporalmente', html_body, settings.DEFAULT_FROM_EMAIL, [email])
                                    msg.attach_alternative(html_body, 'text/html')
                                    msg.send()
                                    # No generamos OTP aquí si el usuario no existe (evitar revelar información)
                        except Exception:
                            pass
                        try:
                            logging.getLogger('security').warning('Cuenta bloqueada por intentos fallidos: %s', (email or username or ''))
                        except Exception:
                            pass
            except Exception:
                pass
            return TokenAuth(success=False, message='Credenciales inválidas o usuario inactivo')

        if not target_user.is_active or not target_user.check_password(password):
            try:
                created = cache.add(key_attempts, 1, timeout=3600)
                if not created:
                    new_val = cache.incr(key_attempts)
                    if isinstance(new_val, int) and new_val >= 30:
                        try:
                            if cache.add(key_notify, 1, timeout=3600):
                                # Notificar a correo real del usuario
                                if getattr(settings, 'EMAIL_ENABLED', False):
                                    recipient = target_user.email
                                    ctx = { 'email': recipient }
                                    html_body = render_to_string('emails/account_locked.html', ctx)
                                    msg = EmailMultiAlternatives('Cuenta bloqueada temporalmente', html_body, settings.DEFAULT_FROM_EMAIL, [recipient])
                                    msg.attach_alternative(html_body, 'text/html')
                                    msg.send()
                                    # Además, generar OTP y enviar el correo de restablecimiento con el mismo diseño
                                    try:
                                        otp_code = str(secrets.randbelow(1000000)).zfill(6)
                                        cache.set(f"pwdotp:{recipient.lower()}", otp_code, timeout=600)
                                        ctx2 = { 'user': target_user, 'code': otp_code }
                                        html2 = render_to_string('emails/password_reset_code.html', ctx2)
                                        msg2 = EmailMultiAlternatives('Código para restablecer contraseña', html2, settings.DEFAULT_FROM_EMAIL, [recipient])
                                        msg2.attach_alternative(html2, 'text/html')
                                        msg2.send()
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                        try:
                            logging.getLogger('security').warning('Cuenta bloqueada por intentos fallidos: %s', target_user.email)
                        except Exception:
                            pass
            except Exception:
                pass
            return TokenAuth(success=False, message='Credenciales inválidas o usuario inactivo')

        user = target_user

        # Generar tokens
        # 1) Tokens GraphQL (para compatibilidad con clientes GraphQL)
        token = graphql_jwt.shortcuts.get_token(user)
        refresh_value = None
        try:
            from graphql_jwt.refresh_token.shortcuts import create_refresh_token
            rt = create_refresh_token(user)
            refresh_value = str(getattr(rt, 'token', rt))
        except Exception:
            refresh_value = None

        # 2) Tokens SimpleJWT (para REST & Swagger vía cookie)
        simple_access = None
        simple_refresh = None
        try:
            srt = DRFRefreshToken.for_user(user)
            simple_refresh = str(srt)
            simple_access = str(srt.access_token)
        except Exception:
            simple_access = None
            simple_refresh = None

        # Resetear contador de fallos al autenticar correctamente
        cache.delete(key_attempts)

        # Poner tokens en el request para que la vista GraphQL pueda setear cookies HttpOnly
        try:
            # Enviar ambos: GraphQL (para GraphQL) y DRF (para REST)
            setattr(request, '_jwt_tokens', {
                'graphql_access': token,
                'graphql_refresh': refresh_value,
                'drf_access': simple_access,
                'drf_refresh': simple_refresh,
            })
        except Exception:
            pass

        # Actualizar last_login manualmente (ruta GraphQL no lo hace por defecto)
        try:
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
        except Exception:
            pass

        return TokenAuth(success=True, token=token, refresh_token=refresh_value, user=user, message='Login exitoso')


class StableRefresh(graphene.Mutation):
    """Refresca el access token sin rotar el refresh token y validando is_active."""

    class Arguments:
        refresh_token = graphene.String(required=False)

    token = graphene.String()
    refresh_token = graphene.String()
    message = graphene.String()

    @staticmethod
    @allow_any
    def mutate(root, info, refresh_token=None):
        request = info.context

        # Obtener refresh token desde argumento o cookie
        jwt_settings = getattr(settings, 'GRAPHQL_JWT', {})
        cookie_name = jwt_settings.get('JWT_REFRESH_TOKEN_COOKIE_NAME', 'JWT_REFRESH_TOKEN')
        token_value = (refresh_token or request.COOKIES.get(cookie_name))
        if not token_value or GQLRefreshToken is None:
            return StableRefresh(token=None, refresh_token=None, message='Refresh token no provisto')

        try:
            rt = GQLRefreshToken.objects.get(token=token_value, revoked__isnull=True)
        except GQLRefreshToken.DoesNotExist:
            return StableRefresh(token=None, refresh_token=None, message='Refresh token inválido')
        except Exception:
            return StableRefresh(token=None, refresh_token=None, message='Error al validar refresh token')

        # Expiración
        if rt.is_expired(request=request):
            return StableRefresh(token=None, refresh_token=None, message='Refresh token expirado')

        user = rt.user
        if not user.is_active:
            return StableRefresh(token=None, refresh_token=None, message='Usuario inactivo')

        access = graphql_jwt.shortcuts.get_token(user)
        # No rotamos ni reusamos el refresh para mantener el mismo valor
        return StableRefresh(token=access, refresh_token=token_value, message='Token refrescado')


class UploadMyPhotoBase64(graphene.Mutation):
    """Sube/actualiza la foto de perfil del usuario autenticado a partir de base64."""

    class Arguments:
        photo_base64 = graphene.String(required=True, description="Cadena base64. Puede incluir prefijo data:image/...;base64,")

    success = graphene.Boolean()
    message = graphene.String()
    photo_url = graphene.String()

    @staticmethod
    @login_required
    def mutate(root, info, photo_base64):
        user = info.context.user
        try:
            data = photo_base64.strip()
            # Eliminar prefijo data URL si existe
            if ',' in data and data.lower().startswith('data:'):
                data = data.split(',', 1)[1]
            try:
                file_bytes = base64.b64decode(data, validate=True)
            except Exception:
                return UploadMyPhotoBase64(success=False, message='Imagen base64 inválida')

            # Límite por configuración
            max_size = int(getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 5 * 1024 * 1024))
            if len(file_bytes) > max_size:
                return UploadMyPhotoBase64(success=False, message='La imagen excede el tamaño máximo permitido')

            # Detectar tipo
            kind = imghdr.what(None, h=file_bytes) or 'jpeg'
            ext = 'jpg' if kind in ('jpeg', 'jpg') else kind
            filename = f"user_{user.id}_{int(time.time())}.{ext}"

            content = ContentFile(file_bytes, name=filename)
            # Guardar
            user.photo.save(filename, content, save=True)

            # Construir URL absoluta
            request = info.context
            url = None
            try:
                url = user.photo.url
                if url and hasattr(request, 'build_absolute_uri'):
                    url = request.build_absolute_uri(url)
            except Exception:
                url = None
            return UploadMyPhotoBase64(success=True, message='Foto actualizada', photo_url=url)
        except Exception as e:
            return UploadMyPhotoBase64(success=False, message=f'Error al subir foto: {str(e)}', photo_url=None)


class UploadMyPhotoUrl(graphene.Mutation):
    """Actualiza la foto de perfil descargando desde una URL pública (HTTP/HTTPS)."""

    class Arguments:
        photo_url = graphene.String(required=True, description="URL pública de la imagen (HTTP/HTTPS)")

    success = graphene.Boolean()
    message = graphene.String()
    photo_url = graphene.String()

    @staticmethod
    @login_required
    def mutate(root, info, photo_url):
        user = info.context.user
        try:
            url = (photo_url or '').strip()
            if not (url.startswith('http://') or url.startswith('https://')):
                return UploadMyPhotoUrl(success=False, message='URL inválida (debe iniciar con http:// o https://)', photo_url=None)

            # Descargar con timeout y tamaño acotado
            max_size = int(getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 5 * 1024 * 1024))
            try:
                resp = requests.get(url, stream=True, timeout=6)
                resp.raise_for_status()
            except Exception:
                return UploadMyPhotoUrl(success=False, message='No se pudo descargar la imagen', photo_url=None)

            content_type = resp.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                return UploadMyPhotoUrl(success=False, message='La URL no apunta a una imagen', photo_url=None)

            # Leer hasta max_size + 1 para detectar exceso
            data = b''
            chunk_size = 64 * 1024
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:
                    data += chunk
                    if len(data) > max_size:
                        return UploadMyPhotoUrl(success=False, message='La imagen excede el tamaño máximo permitido', photo_url=None)

            # Detectar tipo
            kind = imghdr.what(None, h=data) or 'jpeg'
            ext = 'jpg' if kind in ('jpeg', 'jpg') else kind
            # Derivar nombre desde URL
            parsed = urlparse(url)
            base_name = (parsed.path.rsplit('/', 1)[-1] or f'ext_{int(time.time())}').split('?')[0]
            if '.' not in base_name:
                base_name = f"{base_name}.{ext}"
            filename = f"user_{user.id}_{int(time.time())}_{base_name}"

            content = ContentFile(data, name=filename)
            user.photo.save(filename, content, save=True)

            # Construir URL absoluta
            request = info.context
            out_url = None
            try:
                out_url = user.photo.url
                if out_url and hasattr(request, 'build_absolute_uri'):
                    out_url = request.build_absolute_uri(out_url)
            except Exception:
                out_url = None

            return UploadMyPhotoUrl(success=True, message='Foto actualizada', photo_url=out_url)
        except Exception as e:
            return UploadMyPhotoUrl(success=False, message=f'Error al actualizar foto: {str(e)}', photo_url=None)

class ForgotPassword(graphene.Mutation):
    """Envía un código OTP para restablecer la contraseña (con reCAPTCHA y rate limit)."""

    class Arguments:
        email = graphene.String(required=True)
        recaptcha_token = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    # Solo con fines de desarrollo/pruebas cuando no hay envío de email
    code = graphene.String()

    @staticmethod
    @allow_any
    def mutate(root, info, email, recaptcha_token=None):
        request = info.context

        # reCAPTCHA requerido para Forgot Password
        if getattr(settings, 'RECAPTCHA_ENABLED', False):
            if not verify_recaptcha(recaptcha_token, request.META.get('REMOTE_ADDR')):
                return ForgotPassword(success=False, message='reCAPTCHA inválido')

        # Limitar 5 solicitudes por hora por email
        key_req = f"pwdreq:{email.lower()}"
        key_notify = f"pwdreqnotify:{email.lower()}"
        current = cache.get(key_req)
        if isinstance(current, int) and current >= 5:
            # Notificar por correo SOLO una vez por ventana y solo si el usuario existe (evitar enumeración)
            if getattr(settings, 'EMAIL_ENABLED', False):
                try:
                    user_obj = User.objects.filter(email__iexact=email).first()
                    if user_obj and cache.add(key_notify, 1, timeout=3600):
                        ctx = { 'user': user_obj }
                        html_body = render_to_string('emails/password_reset_rate_limited.html', ctx)
                        msg = EmailMultiAlternatives('Has alcanzado el límite de solicitudes', html_body, settings.DEFAULT_FROM_EMAIL, [email])
                        msg.attach_alternative(html_body, 'text/html')
                        msg.send()
                except Exception:
                    pass
            return ForgotPassword(success=False, message='Has superado el límite de solicitudes. Intenta en 1 hora')

        # Dominio permitido
        try:
            domain = email.split('@')[1].lower()
        except Exception:
            domain = ''
        allowed = [d.lower() for d in getattr(settings, 'ALLOWED_EMAIL_DOMAINS', [])]
        if allowed and domain not in allowed:
            # No revelar si existe o no
            return ForgotPassword(success=True, message='Si el correo existe, se enviará un código')

        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email__iexact=email)
        except UserModel.DoesNotExist:
            # Evitar enumeración de usuarios
            # Aun así aumentamos contador para mitigar abuso
            cache.add(key_req, 1, 3600) or cache.incr(key_req)
            return ForgotPassword(success=True, message='Si el correo existe, se enviará un código')

        # Generar código OTP de 6 dígitos, válido 10 min
        code = str(secrets.randbelow(1000000)).zfill(6)
        cache.set(f"pwdotp:{email.lower()}", code, timeout=600)
        # Incrementar contador de solicitudes (ventana 1h)
        cache.add(key_req, 1, 3600) or cache.incr(key_req)

        # Enviar email con el código (solo si está habilitado)
        if getattr(settings, 'EMAIL_ENABLED', False):
            try:
                ctx = { 'user': user, 'code': code }
                html_body = render_to_string('emails/password_reset_code.html', ctx)
                msg = EmailMultiAlternatives('Código para restablecer contraseña', html_body, settings.DEFAULT_FROM_EMAIL, [email])
                msg.attach_alternative(html_body, 'text/html')
                msg.send()
            except Exception:
                pass

        # Exponer código en entorno de desarrollo o cuando no se envían correos
        debug_show_code = (not getattr(settings, 'EMAIL_ENABLED', False)) or getattr(settings, 'DEBUG', False)
        return ForgotPassword(success=True, message='Si el correo existe, se envió un código de verificación', code=(code if debug_show_code else None))


class ResetPasswordWithCode(graphene.Mutation):
    """Restablece contraseña verificando un código OTP enviado al correo."""

    class Arguments:
        email = graphene.String(required=True)
        code = graphene.String(required=True)
        new_password = graphene.String(required=True)
        confirm_password = graphene.String(required=True)
        recaptcha_token = graphene.String(required=False)

    success = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    @allow_any
    def mutate(root, info, email, code, new_password, confirm_password, recaptcha_token=None):
        request = info.context
        # reCAPTCHA no requerido para Reset Password

        if new_password != confirm_password:
            return ResetPasswordWithCode(success=False, message='Las contraseñas no coinciden')
        if len(new_password) < 8:
            return ResetPasswordWithCode(success=False, message='La contraseña debe tener al menos 8 caracteres')

        cached_code = cache.get(f"pwdotp:{email.lower()}")
        if not cached_code or cached_code != code:
            return ResetPasswordWithCode(success=False, message='Código inválido o expirado')

        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email__iexact=email)
        except UserModel.DoesNotExist:
            return ResetPasswordWithCode(success=False, message='Usuario no encontrado')

        user.set_password(new_password)
        user.save(update_fields=['password'])
        cache.delete(f"pwdotp:{email.lower()}")
        return ResetPasswordWithCode(success=True, message='Contraseña actualizada correctamente')


class ChangePassword(graphene.Mutation):
    """Cambio de contraseña para usuario autenticado requiriendo contraseña actual."""

    class Arguments:
        current_password = graphene.String(required=True)
        new_password = graphene.String(required=True)
        confirm_password = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    @login_required
    def mutate(root, info, current_password, new_password, confirm_password):
        user = info.context.user
        if new_password != confirm_password:
            return ChangePassword(success=False, message='Las contraseñas no coinciden')
        if len(new_password) < 8:
            return ChangePassword(success=False, message='La contraseña debe tener al menos 8 caracteres')
        if not user.check_password(current_password):
            return ChangePassword(success=False, message='La contraseña actual es incorrecta')
        user.set_password(new_password)
        user.save(update_fields=['password'])
        return ChangePassword(success=True, message='Contraseña actualizada correctamente')


class DeleteUser(graphene.Mutation):
    """Elimina un usuario (solo ADMINISTRADOR)."""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    @login_required
    def mutate(root, info, id):
        user = info.context.user
        if user.role != 'ADMINISTRADOR':
            return DeleteUser(success=False, message='Solo ADMINISTRADOR puede eliminar usuarios')
        try:
            real_id = _resolve_real_id(id)
            if not real_id:
                return DeleteUser(success=False, message='ID inválido')
            target = User.objects.get(id=real_id)
            target.delete()
            return DeleteUser(success=True, message='Usuario eliminado correctamente')
        except User.DoesNotExist:
            return DeleteUser(success=False, message='Usuario no encontrado')
        except Exception as e:
            return DeleteUser(success=False, message=f'Error al eliminar usuario: {str(e)}')


class Logout(graphene.Mutation):
    """Cierra sesión: revoca refresh token y limpia cookies HttpOnly."""

    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        refresh_token = graphene.String(required=False)

    @staticmethod
    @allow_any
    def mutate(root, info, refresh_token=None):
        request = info.context
        # Intentar obtener refresh token desde argumento o cookie
        token = refresh_token or request.COOKIES.get(getattr(settings, 'GRAPHQL_JWT', {}).get('JWT_REFRESH_TOKEN_COOKIE_NAME', 'JWT_REFRESH_TOKEN'))
        revoked = False
        if token and GQLRefreshToken is not None:
            try:
                obj = GQLRefreshToken.objects.get(token=token)
                obj.revoke()
                revoked = True
            except GQLRefreshToken.DoesNotExist:
                pass
            except Exception:
                pass
        # Señalar al view para limpiar cookies
        setattr(request, '_clear_jwt_cookies', True)
        return Logout(success=True, message='Sesión cerrada' + (' y token revocado' if revoked else ''))


# ===== MUTATIONS PARA ESTUDIANTES =====
class CreateStudent(graphene.Mutation):
    """Mutation para crear un estudiante."""
    
    class Arguments:
        input = StudentInput(required=True)
    
    success = graphene.Boolean()
    student = graphene.Field(StudentType)
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, input):
        user = info.context.user
        if user.role not in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
            return CreateStudent(success=False, message="Sin permisos para crear estudiantes")
        
        try:
            with transaction.atomic():
                target_user = User.objects.get(id=input.user_id)
                if target_user.role != UserRole.PRACTICANTE.value:
                    return CreateStudent(success=False, message="El usuario debe tener rol PRACTICANTE")
                
                student = Student.objects.create(
                    user=target_user,
                    codigo_estudiante=input.codigo_estudiante,
                    documento_tipo=input.documento_tipo,
                    documento_numero=input.documento_numero,
                    telefono=input.telefono,
                    direccion=input.direccion,
                    carrera=input.carrera,
                    semestre_actual=input.semestre_actual,
                    promedio_ponderado=input.promedio_ponderado,
                )
                
                return CreateStudent(
                    success=True,
                    student=student,
                    message="Estudiante creado exitosamente"
                )
        except User.DoesNotExist:
            return CreateStudent(success=False, message="Usuario no encontrado")
        except Exception as e:
            return CreateStudent(success=False, message=f"Error al crear estudiante: {str(e)}")


# ===== MUTATIONS PARA EMPRESAS =====
class CreateCompany(graphene.Mutation):
    """Mutation para crear una empresa."""
    
    class Arguments:
        input = CompanyInput(required=True)
    
    success = graphene.Boolean()
    company = graphene.Field(CompanyType)
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, input):
        user = info.context.user
        if user.role not in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
            return CreateCompany(success=False, message="Sin permisos para crear empresas")
        
        try:
            with transaction.atomic():
                company = Company.objects.create(
                    ruc=input.ruc,
                    razon_social=input.razon_social,
                    nombre_comercial=input.nombre_comercial,
                    direccion=input.direccion,
                    telefono=input.telefono,
                    email=input.email,
                    sector_economico=input.sector_economico,
                    tamaño_empresa=input.tamano_empresa,
                    status=CompanyStatus.PENDING_VALIDATION.value,
                )
                
                return CreateCompany(
                    success=True,
                    company=company,
                    message="Empresa creada exitosamente"
                )
        except Exception as e:
            return CreateCompany(success=False, message=f"Error al crear empresa: {str(e)}")


class ValidateCompany(graphene.Mutation):
    """Mutation para validar una empresa."""
    
    class Arguments:
        company_id = graphene.ID(required=True)
        approve = graphene.Boolean(required=True)
        observations = graphene.String()
    
    success = graphene.Boolean()
    company = graphene.Field(CompanyType)
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, company_id, approve, observations=None):
        user = info.context.user
        if user.role not in ['COORDINADOR', 'ADMINISTRADOR']:
            return ValidateCompany(success=False, message="Sin permisos para validar empresas")
        
        try:
            company = Company.objects.get(id=company_id)
            
            if approve:
                company.status = CompanyStatus.ACTIVE.value
                company.fecha_validacion = timezone.now()
                message = "Empresa aprobada exitosamente"
            else:
                company.status = CompanyStatus.SUSPENDED.value
                message = "Empresa rechazada"
            
            company.save()
            
            return ValidateCompany(
                success=True,
                company=company,
                message=message
            )
        except Company.DoesNotExist:
            return ValidateCompany(success=False, message="Empresa no encontrada")
        except Exception as e:
            return ValidateCompany(success=False, message=f"Error al validar empresa: {str(e)}")


# ===== MUTATIONS PARA PRÁCTICAS =====
class CreatePractice(graphene.Mutation):
    """Mutation para crear una práctica."""
    
    class Arguments:
        input = PracticeInput(required=True)
    
    success = graphene.Boolean()
    practice = graphene.Field(PracticeType)
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, input):
        user = info.context.user
        
        try:
            with transaction.atomic():
                # Verificar permisos
                if user.role == UserRole.PRACTICANTE.value:
                    # El estudiante puede crear su propia práctica
                    student = getattr(user, 'student_profile', None)
                    if not student or str(student.id) != input.student_id:
                        return CreatePractice(success=False, message="Solo puedes crear tu propia práctica")
                elif user.role not in ['COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']:
                    return CreatePractice(success=False, message="Sin permisos para crear prácticas")
                
                # Obtener objetos relacionados
                student = Student.objects.get(id=input.student_id)
                company = Company.objects.get(id=input.company_id)
                supervisor = None
                if input.supervisor_id:
                    supervisor = Supervisor.objects.get(id=input.supervisor_id)
                
                # Validar elegibilidad del estudiante
                if student.semestre_actual < 6:
                    return CreatePractice(success=False, message="Estudiante debe estar en semestre 6 o superior")
                
                if student.promedio_ponderado < 12.0:
                    return CreatePractice(success=False, message="Estudiante debe tener promedio mínimo de 12.0")
                
                # Crear práctica
                practice = Practice.objects.create(
                    student=student,
                    company=company,
                    supervisor=supervisor,
                    titulo=input.titulo,
                    descripcion=input.descripcion or "",
                    objetivos=input.objetivos or [],
                    fecha_inicio=input.fecha_inicio,
                    fecha_fin=input.fecha_fin,
                    horas_totales=input.horas_totales or 0,
                    modalidad=input.modalidad or 'PRESENCIAL',
                    area_practica=input.area_practica,
                    status=PracticeStatus.DRAFT.value,
                )
                
                return CreatePractice(
                    success=True,
                    practice=practice,
                    message="Práctica creada exitosamente"
                )
        except (Student.DoesNotExist, Company.DoesNotExist, Supervisor.DoesNotExist):
            return CreatePractice(success=False, message="Objeto relacionado no encontrado")
        except Exception as e:
            return CreatePractice(success=False, message=f"Error al crear práctica: {str(e)}")


class UpdatePracticeStatus(graphene.Mutation):
    """Mutation para actualizar el estado de una práctica."""
    
    class Arguments:
        practice_id = graphene.ID(required=True)
        status = graphene.String(required=True)
        observations = graphene.String()
    
    success = graphene.Boolean()
    practice = graphene.Field(PracticeType)
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, practice_id, status, observations=None):
        user = info.context.user
        
        try:
            practice = Practice.objects.get(id=practice_id)
            
            # Verificar permisos según el estado y rol
            if status == PracticeStatus.PENDING.value:
                # Solo el estudiante puede enviar a revisión
                if user.role != UserRole.PRACTICANTE.value:
                    return UpdatePracticeStatus(success=False, message="Solo el estudiante puede enviar a revisión")
                if practice.student.user.id != user.id:
                    return UpdatePracticeStatus(success=False, message="Solo puedes modificar tu propia práctica")
            
            elif status in [PracticeStatus.APPROVED.value, PracticeStatus.CANCELLED.value]:
                # Solo coordinadores pueden aprobar/cancelar
                if user.role not in ['COORDINADOR', 'ADMINISTRADOR']:
                    return UpdatePracticeStatus(success=False, message="Sin permisos para aprobar/cancelar prácticas")
            
            elif status == PracticeStatus.IN_PROGRESS.value:
                # El supervisor puede marcar como en progreso
                if user.role == UserRole.SUPERVISOR.value:
                    supervisor = getattr(user, 'supervisor_profile', None)
                    if not supervisor or practice.supervisor.id != supervisor.id:
                        return UpdatePracticeStatus(success=False, message="Solo el supervisor asignado puede modificar")
                elif user.role not in ['COORDINADOR', 'ADMINISTRADOR']:
                    return UpdatePracticeStatus(success=False, message="Sin permisos")
            
            # Actualizar estado
            practice.status = status
            if observations:
                practice.observaciones = observations
            
            practice.save()
            
            return UpdatePracticeStatus(
                success=True,
                practice=practice,
                message=f"Estado actualizado a {status}"
            )
            
        except Practice.DoesNotExist:
            return UpdatePracticeStatus(success=False, message="Práctica no encontrada")
        except Exception as e:
            return UpdatePracticeStatus(success=False, message=f"Error al actualizar estado: {str(e)}")


# ===== MUTATIONS PARA DOCUMENTOS =====


# ===== MUTATIONS PARA NOTIFICACIONES =====
class MarkNotificationAsRead(graphene.Mutation):
    """Mutation para marcar una notificación como leída."""
    
    class Arguments:
        notification_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    notification = graphene.Field(NotificationType)
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, notification_id):
        user = info.context.user
        
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
            notification.leida = True
            notification.fecha_lectura = timezone.now()
            notification.save()
            
            return MarkNotificationAsRead(
                success=True,
                notification=notification,
                message="Notificación marcada como leída"
            )
            
        except Notification.DoesNotExist:
            return MarkNotificationAsRead(success=False, message="Notificación no encontrada")
        except Exception as e:
            return MarkNotificationAsRead(success=False, message=f"Error: {str(e)}")


# ===== MUTATION PRINCIPAL =====
class Mutation(graphene.ObjectType):
    """Mutations principales del sistema."""
    
    # Auth
    token_auth = TokenAuth.Field()
    verify_token = graphql_jwt.Verify.Field()
    # Opción original de la librería (rota el refresh):
    refresh_token = graphql_jwt.Refresh.Field()
    # Opción estable (no rota el refresh):
    stable_refresh = StableRefresh.Field()
    forgot_password = ForgotPassword.Field()
    reset_password_with_code = ResetPasswordWithCode.Field()
    change_password = ChangePassword.Field()
    logout = Logout.Field()

    # Usuarios
    create_user = CreateUser.Field()
    update_user = UpdateUser.Field()
    delete_user = DeleteUser.Field()
    update_my_profile = UpdateMyProfile.Field()
    upload_my_photo_base64 = UploadMyPhotoBase64.Field()
    upload_my_photo_url = UploadMyPhotoUrl.Field()
    
    # Estudiantes
    create_student = CreateStudent.Field()
    
    # Empresas
    create_company = CreateCompany.Field()
    validate_company = ValidateCompany.Field()
    
    # Prácticas
    create_practice = CreatePractice.Field()
    update_practice_status = UpdatePracticeStatus.Field()
    
    # Notificaciones
    mark_notification_as_read = MarkNotificationAsRead.Field()
