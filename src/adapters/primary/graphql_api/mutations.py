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
from src.infrastructure.security.tasks import send_welcome_email
from src.infrastructure.security.decorators import sanitize_mutation_input
from src.infrastructure.security.sanitizers import sanitize_text_field
from rest_framework.throttling import AnonRateThrottle

from .types import (
    UserType, StudentType, CompanyType, SupervisorType,
    PracticeType, DocumentType, NotificationType,
    UserInput, UserUpdateInput, ProfileInput, StudentInput, CompanyInput,
    PracticeInput
)
from .permissions_mutations import GrantUserPermission, RevokeUserPermission
from src.adapters.secondary.database.models import (
    Student, Company, Supervisor, Practice, Document, Notification, Avatar,
    Role, Permission
)
from src.domain.enums import UserRole, PracticeStatus, CompanyStatus
from src.infrastructure.security.cloudflare_turnstile import verify_turnstile_token

User = get_user_model()


class ForgotPasswordThrottle(AnonRateThrottle):
    """Throttle personalizado para forgot password."""
    scope = 'password_reset'


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
    @sanitize_mutation_input(
        text_fields=['email', 'username', 'first_name', 'last_name', 'codigo_estudiante']
    )
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
                # Enviar correo de bienvenida (COMENTADO - servidor de correo no configurado)
                # if getattr(settings, 'EMAIL_ENABLED', False):
                #     try:
                #         send_welcome_email.delay(str(new_user.id))
                #     except Exception:
                #         try:
                #             ctx = { 
                #                 'user': new_user, 
                #                 'frontend_url': getattr(settings, 'FRONTEND_URL', '') 
                #             }
                #             html_body = render_to_string('emails/user_welcome.html', ctx)
                #             msg = EmailMultiAlternatives(
                #                 'Bienvenido al Sistema de Prácticas',
                #                 html_body,
                #                 settings.DEFAULT_FROM_EMAIL,
                #                 [new_user.email]
                #             )
                #             msg.attach_alternative(html_body, 'text/html')
                #             msg.send()
                #         except Exception:
                #             pass
                
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
            
            # Actualizar campos (RESTRICCIONES: Administrador NO puede editar username, email, ni password)
            if input.email:
                return UpdateUser(success=False, message='El administrador no puede editar el email del usuario')
            if getattr(input, 'username', None):
                return UpdateUser(success=False, message='El administrador no puede editar el username del usuario')
            if input.password:
                return UpdateUser(success=False, message='El administrador no puede editar la contraseña del usuario')
            
            # Campos que SÍ puede editar el administrador
            if input.first_name:
                target_user.first_name = input.first_name
            if input.last_name:
                target_user.last_name = input.last_name
            if input.role:
                target_user.role = input.role
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
    """Actualiza el perfil del usuario autenticado (solo nombres y apellidos)."""

    class Arguments:
        input = ProfileInput(required=True)

    success = graphene.Boolean()
    user = graphene.Field(UserType)
    message = graphene.String()

    @staticmethod
    @login_required
    @sanitize_mutation_input(
        text_fields=['first_name', 'last_name']
    )
    def mutate(root, info, input):
        user = info.context.user
        try:
            changed = False
            
            # Solo se pueden editar nombres y apellidos
            if getattr(input, 'first_name', None):
                user.first_name = (input.first_name or '').strip()
                changed = True
            if getattr(input, 'last_name', None):
                user.last_name = (input.last_name or '').strip()
                changed = True

            if changed:
                user.save(update_fields=['first_name','last_name','updated_at'])
                return UpdateMyProfile(success=True, user=user, message='Perfil actualizado')
            else:
                return UpdateMyProfile(success=True, user=user, message='Sin cambios')
        except Exception as e:
            return UpdateMyProfile(success=False, message=f'Error al actualizar perfil: {str(e)}')


# ===== AUTH MUTATIONS (LOGIN / PASSWORD RESET) =====
# NOTA: TokenAuth y StableRefresh están OBSOLETOS - usar jwtLogin de jwt_mutations.py

class ForgotPassword(graphene.Mutation):
    """Envía un código OTP para restablecer la contraseña (con Cloudflare Turnstile y rate limit)."""

    class Arguments:
        email = graphene.String(required=True)
        cloudflare_token = graphene.String(required=False)

    success = graphene.Boolean()
    message = graphene.String()
    # Solo con fines de desarrollo/pruebas cuando no hay envío de email
    code = graphene.String()

    @staticmethod
    @allow_any
    def mutate(root, info, email, cloudflare_token=None):
        
        from django.core.cache import cache
        from django.contrib.auth import get_user_model
        from django.conf import settings
        from django.template.loader import render_to_string
        from django.core.mail import EmailMultiAlternatives
        from src.infrastructure.security.cloudflare_turnstile import verify_turnstile_token
        from src.infrastructure.security.logging import security_event_logger, get_client_ip
        import secrets
        
        # Importar Django Axes de forma segura
        try:
            from axes.helpers import get_failure_limit, is_locked
            from axes.utils import reset
            AXES_AVAILABLE = True
        except ImportError:
            AXES_AVAILABLE = False

        User = get_user_model()
        request = info.context
        ip_address = get_client_ip(request)

        # Verificación DRF Throttling
        throttle = ForgotPasswordThrottle()
        if not throttle.allow_request(request, None):
            return ForgotPassword(success=False, message='Demasiadas solicitudes. Intenta más tarde.')

        # Verificación Cloudflare Turnstile
        if getattr(settings, 'CLOUDFLARE_TURNSTILE_ENABLED', False):
            if not verify_turnstile_token(cloudflare_token, request.META.get('REMOTE_ADDR')):
                return ForgotPassword(success=False, message='Verificación de seguridad fallida')

        # Verificar si está bloqueado por Django Axes
        if AXES_AVAILABLE and is_locked(request, credentials={'email': email}):
            security_event_logger.log_security_event(
                'forgot_password_blocked',
                f"Forgot password blocked by Axes for email: {email}",
                extra_data={
                    'email': email,
                    'ip_address': ip_address,
                    'reason': 'axes_locked'
                },
                severity='WARNING'
            )
            return ForgotPassword(success=False, message='Demasiados intentos. Intenta más tarde.')

        # Rate limiting básico con DRF (5 intentos por hora por email)
        key_req = f"forgot_pwd:{email.lower()}"
        current = cache.get(key_req, 0)
        if current >= 5:
            return ForgotPassword(success=False, message='Demasiadas solicitudes. Intenta en 1 hora.')

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
            
            # Log intento fallido y registrar en Axes
            security_event_logger.log_security_event(
                'forgot_password_failed',
                f"Forgot password attempt for non-existent email: {email}",
                extra_data={
                    'email': email,
                    'ip_address': ip_address,
                    'reason': 'user_not_found'
                },
                severity='WARNING'
            )
            
            # Incrementar contador de rate limiting
            cache.set(key_req, current + 1, timeout=3600)
            
            # Evitar enumeración de usuarios
            return ForgotPassword(success=True, message='Si el correo existe, se enviará un código')

        # Generar código OTP de 6 dígitos, válido 10 min
        code = str(secrets.randbelow(1000000)).zfill(6)
        cache.set(f"pwdotp:{email.lower()}", code, timeout=600)
        
        # Incrementar contador de rate limiting (también para exitosos)
        cache.set(key_req, current + 1, timeout=3600)
        
        # Log intento exitoso
        security_event_logger.log_security_event(
            'forgot_password_success',
            f"Forgot password code generated for email: {email}",
            user_id=str(user.id),
            extra_data={
                'email': email,
                'ip_address': ip_address
            },
            severity='INFO'
        )
        

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

        # SIEMPRE mostrar código en desarrollo (cuando EMAIL no está habilitado)
        email_enabled = getattr(settings, 'EMAIL_ENABLED', False)
        debug_mode = getattr(settings, 'DEBUG', False)
        
        # Mostrar código si EMAIL está deshabilitado O si estamos en DEBUG
        show_code = (not email_enabled) or debug_mode
        
        if show_code:
            message = f'✅ Código generado: {code}. También visible en terminal del backend.'
        else:
            message = 'Si el correo existe, se envió un código de verificación'
            
        return ForgotPassword(success=True, message=message, code=code if show_code else None)


class ResetPasswordWithCode(graphene.Mutation):
    """Restablece contraseña verificando un código OTP enviado al correo."""

    class Arguments:
        email = graphene.String(required=True)
        code = graphene.String(required=True)
        new_password = graphene.String(required=True)
        confirm_password = graphene.String(required=True)
        cloudflare_token = graphene.String(required=False)

    success = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    @allow_any
    def mutate(root, info, email, code, new_password, confirm_password, cloudflare_token=None):
        request = info.context
        # Cloudflare Turnstile no requerido para Reset Password

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
    @sanitize_mutation_input(
        text_fields=['ruc', 'razon_social', 'nombre_comercial', 'direccion', 'telefono', 'email', 'sector_economico', 'tamano_empresa']
    )
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
    @sanitize_mutation_input(
        text_fields=['titulo', 'area_practica', 'modalidad'],
        rich_text_fields=['descripcion']
    )
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


# ===== MUTACIONES DE AVATARES =====
class SelectMyAvatar(graphene.Mutation):
    """Selecciona un avatar por ID para el usuario autenticado."""
    
    class Arguments:
        avatar_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    user = graphene.Field(UserType)
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, avatar_id):
        user = info.context.user
        
        try:
            # Obtener el avatar por ID
            avatar = Avatar.objects.get(id=avatar_id, is_active=True)
            
            # Verificar que el avatar corresponde al rol del usuario
            if avatar.role != user.role:
                return SelectMyAvatar(
                    success=False, 
                    message=f"Este avatar no está disponible para tu rol ({user.role})"
                )
            
            # Asignar el avatar al usuario
            user.avatar = avatar
            user.save()
            
            return SelectMyAvatar(
                success=True,
                user=user,
                message="Avatar seleccionado correctamente"
            )
            
        except Avatar.DoesNotExist:
            return SelectMyAvatar(success=False, message="Avatar no encontrado")
        except Exception as e:
            return SelectMyAvatar(success=False, message=f"Error: {str(e)}")


class RemoveMyAvatar(graphene.Mutation):
    """Elimina la relación de avatar del usuario autenticado."""
    
    success = graphene.Boolean()
    user = graphene.Field(UserType)
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info):
        user = info.context.user
        
        try:
            # Eliminar la relación con el avatar
            user.avatar = None
            user.save()
            
            return RemoveMyAvatar(
                success=True,
                user=user,
                message="Avatar eliminado correctamente"
            )
            
        except Exception as e:
            return RemoveMyAvatar(success=False, message=f"Error: {str(e)}")


# ===== MUTACIONES DE GESTIÓN DE AVATARES (ADMIN) =====
class CreateAvatar(graphene.Mutation):
    """Crea un nuevo avatar (solo ADMIN)."""
    
    class Arguments:
        url = graphene.String(required=True)
        role = graphene.String(required=True)
        is_active = graphene.Boolean()
    
    success = graphene.Boolean()
    message = graphene.String()
    avatar = graphene.Field('src.adapters.primary.graphql_api.types.AvatarType')
    
    @staticmethod
    @login_required
    def mutate(root, info, url, role, is_active=True):
        user = info.context.user
        
        # Solo ADMINISTRADOR puede crear avatares
        if user.role != 'ADMINISTRADOR':
            return CreateAvatar(
                success=False, 
                message="Solo los administradores pueden crear avatares"
            )
        
        try:
            # Validar rol
            valid_roles = ['PRACTICANTE', 'SUPERVISOR', 'COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR']
            if role not in valid_roles:
                return CreateAvatar(
                    success=False, 
                    message=f"Rol inválido. Debe ser uno de: {', '.join(valid_roles)}"
                )
            
            # Crear avatar
            avatar = Avatar.objects.create(
                url=url,
                role=role,
                is_active=is_active
            )
            
            return CreateAvatar(
                success=True,
                message="Avatar creado correctamente",
                avatar=avatar
            )
            
        except Exception as e:
            return CreateAvatar(success=False, message=f"Error: {str(e)}")


class UpdateAvatar(graphene.Mutation):
    """Actualiza un avatar existente (solo ADMIN)."""
    
    class Arguments:
        id = graphene.ID(required=True)
        url = graphene.String()
        is_active = graphene.Boolean()
    
    success = graphene.Boolean()
    message = graphene.String()
    avatar = graphene.Field('src.adapters.primary.graphql_api.types.AvatarType')
    
    @staticmethod
    @login_required
    def mutate(root, info, id, url=None, is_active=None):
        user = info.context.user
        
        # Solo ADMINISTRADOR puede actualizar avatares
        if user.role != 'ADMINISTRADOR':
            return UpdateAvatar(
                success=False, 
                message="Solo los administradores pueden actualizar avatares"
            )
        
        try:
            avatar = Avatar.objects.get(id=id)
            
            # Actualizar campos si se proporcionan
            updated = False
            if url is not None:
                avatar.url = url
                updated = True
            if is_active is not None:
                avatar.is_active = is_active
                updated = True
            
            if updated:
                avatar.save()
                return UpdateAvatar(
                    success=True,
                    message="Avatar actualizado correctamente",
                    avatar=avatar
                )
            else:
                return UpdateAvatar(
                    success=True,
                    message="Sin cambios",
                    avatar=avatar
                )
            
        except Avatar.DoesNotExist:
            return UpdateAvatar(success=False, message="Avatar no encontrado")
        except Exception as e:
            return UpdateAvatar(success=False, message=f"Error: {str(e)}")


class DeleteAvatar(graphene.Mutation):
    """Elimina un avatar (solo ADMIN)."""
    
    class Arguments:
        id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, id):
        user = info.context.user
        
        # Solo ADMINISTRADOR puede eliminar avatares
        if user.role != 'ADMINISTRADOR':
            return DeleteAvatar(
                success=False, 
                message="Solo los administradores pueden eliminar avatares"
            )
        
        try:
            avatar = Avatar.objects.get(id=id)
            
            # Verificar si hay usuarios usando este avatar
            users_count = User.objects.filter(avatar=avatar).count()
            if users_count > 0:
                return DeleteAvatar(
                    success=False, 
                    message=f"No se puede eliminar. {users_count} usuario(s) están usando este avatar"
                )
            
            avatar.delete()
            
            return DeleteAvatar(
                success=True,
                message="Avatar eliminado correctamente"
            )
            
        except Avatar.DoesNotExist:
            return DeleteAvatar(success=False, message="Avatar no encontrado")
        except Exception as e:
            return DeleteAvatar(success=False, message=f"Error: {str(e)}")


# ===== MUTACIONES DE GESTIÓN DE PERMISOS DE ROLES (ADMIN) =====
class AddPermissionToRole(graphene.Mutation):
    """Agrega un permiso a un rol (solo ADMIN)."""
    
    class Arguments:
        role_code = graphene.String(required=True)
        permission_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    role = graphene.Field('src.adapters.primary.graphql_api.types.RoleType')
    
    @staticmethod
    @login_required
    def mutate(root, info, role_code, permission_id):
        user = info.context.user
        
        # Solo ADMINISTRADOR puede gestionar permisos de roles
        if user.role != 'ADMINISTRADOR':
            return AddPermissionToRole(
                success=False, 
                message="Solo los administradores pueden gestionar permisos de roles"
            )
        
        try:
            # Validar que el rol existe y no es PRACTICANTE
            if role_code == 'PRACTICANTE':
                return AddPermissionToRole(
                    success=False, 
                    message="No se pueden modificar los permisos del rol PRACTICANTE"
                )
            
            role = Role.objects.get(code=role_code)
            permission = Permission.objects.get(id=permission_id)
            
            # Verificar si ya tiene el permiso
            if role.permissions.filter(id=permission_id).exists():
                return AddPermissionToRole(
                    success=False, 
                    message=f"El rol {role_code} ya tiene el permiso {permission.code}"
                )
            
            # Agregar permiso al rol
            role.permissions.add(permission)
            
            return AddPermissionToRole(
                success=True,
                message=f"Permiso {permission.code} agregado al rol {role_code}",
                role=role
            )
            
        except Role.DoesNotExist:
            return AddPermissionToRole(success=False, message=f"Rol {role_code} no encontrado")
        except Permission.DoesNotExist:
            return AddPermissionToRole(success=False, message="Permiso no encontrado")
        except Exception as e:
            return AddPermissionToRole(success=False, message=f"Error: {str(e)}")


class RemovePermissionFromRole(graphene.Mutation):
    """Elimina un permiso de un rol (solo ADMIN)."""
    
    class Arguments:
        role_code = graphene.String(required=True)
        permission_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    role = graphene.Field('src.adapters.primary.graphql_api.types.RoleType')
    
    @staticmethod
    @login_required
    def mutate(root, info, role_code, permission_id):
        user = info.context.user
        
        # Solo ADMINISTRADOR puede gestionar permisos de roles
        if user.role != 'ADMINISTRADOR':
            return RemovePermissionFromRole(
                success=False, 
                message="Solo los administradores pueden gestionar permisos de roles"
            )
        
        try:
            # Validar que el rol existe y no es PRACTICANTE
            if role_code == 'PRACTICANTE':
                return RemovePermissionFromRole(
                    success=False, 
                    message="No se pueden modificar los permisos del rol PRACTICANTE"
                )
            
            role = Role.objects.get(code=role_code)
            permission = Permission.objects.get(id=permission_id)
            
            # Verificar si tiene el permiso
            if not role.permissions.filter(id=permission_id).exists():
                return RemovePermissionFromRole(
                    success=False, 
                    message=f"El rol {role_code} no tiene el permiso {permission.code}"
                )
            
            # Eliminar permiso del rol
            role.permissions.remove(permission)
            
            return RemovePermissionFromRole(
                success=True,
                message=f"Permiso {permission.code} eliminado del rol {role_code}",
                role=role
            )
            
        except Role.DoesNotExist:
            return RemovePermissionFromRole(success=False, message=f"Rol {role_code} no encontrado")
        except Permission.DoesNotExist:
            return RemovePermissionFromRole(success=False, message="Permiso no encontrado")
        except Exception as e:
            return RemovePermissionFromRole(success=False, message=f"Error: {str(e)}")


# ===== MUTATION PRINCIPAL =====
class Mutation(graphene.ObjectType):
    """Mutaciones disponibles en el sistema."""
    
    # Autenticación JWT PURO (PRINCIPAL)
    # Estas se importarán dinámicamente del archivo jwt_mutations.py
    
    # Autenticación JWT (HABILITADA - Sistema JWT PURO)
    # token_auth = TokenAuth.Field()
    # verify_token = graphql_jwt.Verify.Field()
    # refresh_token = graphql_jwt.Refresh.Field()
    # stable_refresh = StableRefresh.Field()
    
    # Recuperación de contraseña (mantener)
    forgot_password = ForgotPassword.Field()
    reset_password_with_code = ResetPasswordWithCode.Field()
    change_password = ChangePassword.Field()
    logout = Logout.Field()
    create_user = CreateUser.Field()
    update_user = UpdateUser.Field()
    delete_user = DeleteUser.Field()
    update_my_profile = UpdateMyProfile.Field()
    
    # Estudiantes
    create_student = CreateStudent.Field()
    
    # Empresas
    create_company = CreateCompany.Field()
    validate_company = ValidateCompany.Field()
    
    # Prácticas
    create_practice = CreatePractice.Field()
    update_practice_status = UpdatePracticeStatus.Field()
    
    # Sesiones Opacas (nuevo sistema)
    opaque_login = None  # Se importará dinámicamente
    opaque_logout = None  # Se importará dinámicamente
    extend_opaque_session = None  # Se importará dinámicamente
    
    # Notificaciones
    mark_notification_as_read = MarkNotificationAsRead.Field()
    
    # Avatares
    select_my_avatar = SelectMyAvatar.Field()
    remove_my_avatar = RemoveMyAvatar.Field()
    
    # Gestión de Avatares (ADMIN)
    create_avatar = CreateAvatar.Field()
    update_avatar = UpdateAvatar.Field()
    delete_avatar = DeleteAvatar.Field()
    
    # Gestión de Permisos de Roles (ADMIN)
    add_permission_to_role = AddPermissionToRole.Field()
    remove_permission_from_role = RemovePermissionFromRole.Field()
    
    # Gestión de Permisos de Usuario (ADMIN)
    grant_user_permission = GrantUserPermission.Field()
    revoke_user_permission = RevokeUserPermission.Field()
