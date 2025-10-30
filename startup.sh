#!/bin/bash
# =====================================================
# STARTUP SCRIPT FOR AZURE APP SERVICE
# Sistema de Gestión de Prácticas Profesionales - UPeU
# =====================================================
# This script runs when Azure App Service container starts

set -e  # Exit on error

echo "🚀 Starting UPEU PPP System on Azure..."
echo "========================================"

# =====================================================
# 1. ENVIRONMENT INFO
# =====================================================
echo ""
echo "📊 Environment Information:"
echo "- Python version: $(python --version)"
echo "- Working directory: $(pwd)"
echo "- User: $(whoami)"
echo "- Environment: ${DJANGO_SETTINGS_MODULE:-Not set}"

# =====================================================
# 2. INSTALL/UPDATE DEPENDENCIES
# =====================================================
echo ""
echo "📦 Installing/Updating dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements/production.txt --quiet
echo "✅ Dependencies ready"

# =====================================================
# 3. COLLECT STATIC FILES
# =====================================================
echo ""
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput --clear
echo "✅ Static files collected to: ${STATIC_ROOT:-./staticfiles}"

# =====================================================
# 4. RUN MIGRATIONS
# =====================================================
echo ""
echo "🗄️  Running database migrations..."
python manage.py migrate --noinput
echo "✅ Database migrations completed"

# =====================================================
# 5. CREATE CACHE TABLE
# =====================================================
echo ""
echo "💾 Creating cache tables..."
python manage.py createcachetable 2>/dev/null || echo "⚠️  Cache table exists or not needed"

# =====================================================
# 6. WARMUP CACHE (Optional)
# =====================================================
# Uncomment to warmup cache on startup
# echo ""
# echo "🔥 Warming up cache..."
# python manage.py warmup_cache

# =====================================================
# 7. DEPLOYMENT CHECKS
# =====================================================
echo ""
echo "🔍 Running deployment checks..."
python manage.py check --deploy --fail-level WARNING || echo "⚠️  Non-critical warnings detected"

# =====================================================
# 8. CREATE SUPERUSER (First deployment only)
# =====================================================
echo ""
echo "👤 Checking for superuser..."
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@upeu.edu.pe')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'AdminUPeU2024!')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"✅ Superuser '{username}' created successfully")
else:
    print(f"ℹ️  Superuser '{username}' already exists")
EOF

# =====================================================
# 9. LOAD INITIAL DATA (Optional)
# =====================================================
# Uncomment to load fixtures
# echo ""
# echo "📥 Loading initial data..."
# python manage.py loaddata initial_data.json

# =====================================================
# 10. START APPLICATION SERVER
# =====================================================
echo ""
echo "========================================"
echo "🌐 Starting Gunicorn application server..."
echo "========================================"

# Get configuration from environment or use defaults
PORT=${PORT:-8000}
WORKERS=${GUNICORN_WORKERS:-4}
THREADS=${GUNICORN_THREADS:-2}
TIMEOUT=${GUNICORN_TIMEOUT:-120}
WORKER_CLASS=${GUNICORN_WORKER_CLASS:-sync}

echo "Configuration:"
echo "- Port: $PORT"
echo "- Workers: $WORKERS"
echo "- Threads per worker: $THREADS"
echo "- Timeout: $TIMEOUT seconds"
echo "- Worker class: $WORKER_CLASS"
echo ""

# Start Gunicorn with optimal settings for Azure
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:$PORT" \
    --workers "$WORKERS" \
    --threads "$THREADS" \
    --timeout "$TIMEOUT" \
    --worker-class "$WORKER_CLASS" \
    --worker-tmp-dir /dev/shm \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output \
    --enable-stdio-inheritance

# =====================================================
# NOTES:
# =====================================================
# Configure in Azure App Service:
# 1. Settings -> Configuration -> General settings
#    - Stack: Python 3.11
#    - Startup Command: bash startup.sh
#
# 2. Environment Variables:
#    - DJANGO_SETTINGS_MODULE=config.settings
#    - WEBSITE_HTTPLOGGING_RETENTION_DAYS=7
#    - DJANGO_SUPERUSER_USERNAME=admin
#    - DJANGO_SUPERUSER_EMAIL=admin@upeu.edu.pe
#    - DJANGO_SUPERUSER_PASSWORD=<secure-password>
