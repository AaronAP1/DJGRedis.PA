from django.apps import AppConfig


class DatabaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.adapters.secondary.database'
    verbose_name = 'Base de Datos'
