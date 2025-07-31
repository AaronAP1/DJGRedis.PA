"""
Configuración de Celery para tareas asíncronas.
"""

import os
from celery import Celery
from django.conf import settings

# Establecer la configuración por defecto de Django para el programa 'celery'.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('gestion_practicas')

# Usar la configuración de Django para configurar Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Cargar módulos de tareas de todas las aplicaciones Django registradas.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Tarea de depuración."""
    print(f'Request: {self.request!r}')
