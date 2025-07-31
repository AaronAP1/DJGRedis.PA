from django.apps import AppConfig


class RestApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.adapters.primary.rest_api'
    verbose_name = 'API REST'
