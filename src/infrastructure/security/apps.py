from django.apps import AppConfig


class SecurityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.infrastructure.security'
    label = 'infrastructure_security'
    verbose_name = 'Security Infrastructure'

    def ready(self):
        # Import signal handlers
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Avoid crashes if optional deps (axes) are missing during initial setup
            pass
