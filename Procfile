# =====================================================
# PROCFILE - RENDER DEPLOYMENT
# Sistema de Gestión de Prácticas Profesionales - UPeU
# =====================================================
# Este archivo define los procesos a ejecutar en Render
# Usar solo si NO estás usando render.yaml

# Web Server - Django with Gunicorn
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile -

# Celery Worker - Asynchronous task processor
worker: celery -A config worker --loglevel=info --concurrency=2 --max-tasks-per-child=1000

# Celery Beat - Periodic task scheduler
beat: celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# =====================================================
# NOTAS:
# =====================================================
# 1. Render ejecuta automáticamente el proceso 'web'
# 2. Para worker y beat, crear servicios separados tipo "Background Worker"
# 3. Ajustar --workers según el plan de Render:
#    - Free/Starter: 2 workers
#    - Standard: 4 workers
#    - Pro: 8+ workers
# 4. --timeout 120 permite requests largos (2 minutos)
# 5. --max-tasks-per-child evita memory leaks en Celery
