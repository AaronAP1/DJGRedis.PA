#!/bin/bash
set -e

echo "🚀 Starting Django Application..."

# Esperar a que PostgreSQL esté listo (opcional, útil en local)
if [ -n "$DATABASE_URL" ]; then
    echo "⏳ Waiting for database..."
    sleep 2
fi

# Recolectar archivos estáticos
echo "📦 Collecting static files..."
python manage.py collectstatic --no-input --clear

# Ejecutar migraciones
echo "🔄 Running migrations..."
python manage.py migrate --no-input

# Crear superusuario si no existe (solo en desarrollo)
if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
    echo "👤 Creating superuser..."
    python manage.py createsuperuser --no-input --username "$DJANGO_SUPERUSER_USERNAME" --email "$DJANGO_SUPERUSER_EMAIL" || true
fi

echo "✅ Application ready!"

# Iniciar Gunicorn
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WEB_CONCURRENCY:-3} \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
