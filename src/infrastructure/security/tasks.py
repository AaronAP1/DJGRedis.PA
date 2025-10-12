from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


@shared_task
def send_email_html(subject: str, template_path: str, context: dict, to_email: str) -> bool:
    # Si el envío de correos está deshabilitado, no ejecutar
    if not getattr(settings, 'EMAIL_ENABLED', False):
        return False
    try:
        html_body = render_to_string(template_path, context)
        msg = EmailMultiAlternatives(subject, html_body, settings.DEFAULT_FROM_EMAIL, [to_email])
        msg.attach_alternative(html_body, 'text/html')
        msg.send()
        return True
    except Exception:
        return False


@shared_task
def send_welcome_email(user_id: str) -> bool:
    """Envía email de bienvenida sin credenciales."""
    # Si el envío de correos está deshabilitado, no ejecutar
    if not getattr(settings, 'EMAIL_ENABLED', False):
        return False
    try:
        from src.adapters.secondary.database.models import User

        user = User.objects.get(id=user_id)

        # Contexto del email (sin credenciales)
        ctx = {
            "user": user, 
            "frontend_url": getattr(settings, 'FRONTEND_URL', '')
        }
        
        return send_email_html(
            "Bienvenido al Sistema de Prácticas", 
            "emails/user_welcome.html", 
            ctx, 
            user.email
        )
    except Exception:
        return False
