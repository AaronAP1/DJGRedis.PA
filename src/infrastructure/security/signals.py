from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import settings

@receiver(post_migrate)
def bootstrap_demo_data(sender, **kwargs):
    """Crea admin por defecto y usuarios demo por rol si está habilitado."""
    try:
        from src.adapters.secondary.database.models import User, Student, Company, Supervisor
    except Exception:
        return

    # Crear admin por defecto si no existe
    try:
        admin_email = getattr(settings, 'DEFAULT_ADMIN_EMAIL', 'admin@upeu.edu.pe')
        admin_pass = getattr(settings, 'DEFAULT_ADMIN_PASSWORD', 'Admin123!')
        if not User.objects.filter(email__iexact=admin_email).exists():
            User.objects.create_superuser(
                email=admin_email,
                password=admin_pass,
                first_name='Admin',
                last_name='General',
                role='ADMINISTRADOR',
            )
    except Exception:
        # No bloquear migraciones por datos demo
        pass

    # Crear datos demo opcionales
    if not getattr(settings, 'BOOTSTRAP_DEMO_DATA', False):
        return

    # Coordinador
    try:
        if not User.objects.filter(email__iexact='coordinador@upeu.edu.pe').exists():
            User.objects.create_user(
                email='coordinador@upeu.edu.pe',
                password='Demo123!',
                first_name='Coord',
                last_name='Demo',
                role='COORDINADOR',
                is_active=True,
            )
    except Exception:
        pass

    # Secretaria
    try:
        if not User.objects.filter(email__iexact='secretaria@upeu.edu.pe').exists():
            User.objects.create_user(
                email='secretaria@upeu.edu.pe',
                password='Demo123!',
                first_name='Secre',
                last_name='Demo',
                role='SECRETARIA',
                is_active=True,
            )
    except Exception:
        pass

    # Empresa demo y supervisor
    try:
        company = Company.objects.filter(ruc='20123456789').first()
        if not company:
            company = Company.objects.create(
                ruc='20123456789',
                razon_social='DEMO S.A.C.',
                nombre_comercial='DemoCo',
                direccion='Av. Demo 123',
                telefono='999999999',
                email='contacto@democo.com',
                status='ACTIVE',
            )
        if not User.objects.filter(email__iexact='supervisor@upeu.edu.pe').exists():
            sup_user = User.objects.create_user(
                email='supervisor@upeu.edu.pe',
                password='Demo123!',
                first_name='Sup',
                last_name='Demo',
                role='SUPERVISOR',
                is_active=True,
            )
            Supervisor.objects.create(
                user=sup_user,
                company=company,
                documento_tipo='DNI',
                documento_numero='12345678',
                cargo='Supervisor',
            )
    except Exception:
        pass

    # Practicante
    try:
        if not User.objects.filter(email__iexact='practicante@upeu.edu.pe').exists():
            stu_user = User.objects.create_user(
                email='practicante@upeu.edu.pe',
                password='Demo123!',
                first_name='Stu',
                last_name='Demo',
                role='PRACTICANTE',
                is_active=True,
            )
            Student.objects.create(
                user=stu_user,
                codigo_estudiante='2021000001',
                documento_tipo='DNI',
                documento_numero='00000001',
            )
    except Exception:
        pass
