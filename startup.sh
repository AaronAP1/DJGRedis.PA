﻿#!/bin/bash
set -e

# Configuración de entorno
export HOME="/home"
export PYTHONPATH="/home/site/wwwroot:/opt/python/3.11.13/lib/python3.11/site-packages:$PYTHONPATH"
export PATH="/opt/python/3.11.13/bin:/home/site/wwwroot:$PATH"
export DJANGO_SETTINGS_MODULE="config.settings"
export WSGI_APP="config.wsgi:application"

# Cambiar al directorio de la aplicación
cd /home/site/wwwroot

echo "Starting UPEU PPP API..."
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"

# Crear directorio virtual env si no existe
python -m venv /home/site/wwwroot/env || echo "Virtual env already exists"

# Activar entorno virtual
source /home/site/wwwroot/env/bin/activate

# Asegurar que los paquetes están instalados
python -m pip install --upgrade pip
python -m pip install gunicorn
python -m pip install -r requirements.txt --no-cache-dir

# Verificar la instalación de Django
python -c "import django; print('Django version:', django.get_version())"

# Ejecutar migraciones y recolectar estáticos
echo "Running migrations..."
python manage.py migrate --noinput || echo "Migrations skipped"
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Static skipped"

# Iniciar Gunicorn con configuración específica para Azure
echo "Starting Gunicorn..."
cd /home/site/wwwroot && \
exec gunicorn \
    --bind=0.0.0.0:8000 \
    --timeout 600 \
    --workers 2 \
    --access-logfile - \
    --error-logfile - \
    --log-level debug \
    --capture-output \
    --enable-stdio-inheritance \
    ${WSGI_APP}
