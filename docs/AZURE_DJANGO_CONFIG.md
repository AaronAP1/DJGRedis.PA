# ⚙️ Configuración de Django para Azure

## 📋 Ajustes necesarios en el proyecto

### **1. Archivo `settings_azure.py`**

Crear archivo de configuración específico para Azure:

```python
"""
settings_azure.py - Configuración para Azure App Service
"""
from .settings import *
import os

# ============================================================================
# SEGURIDAD EN PRODUCCIÓN
# ============================================================================

DEBUG = False

SECRET_KEY = os.environ.get('SECRET_KEY')

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# HTTPS enforcement
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ============================================================================
# BASE DE DATOS - Azure Database for PostgreSQL
# ============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),  # psql-upeu-ppp-prod.postgres.database.azure.com
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',  # Forzar SSL
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 600,  # Connection pooling
        'ATOMIC_REQUESTS': True,
    }
}

# ============================================================================
# CACHE - Azure Cache for Redis
# ============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),  # rediss://... (con SSL)
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': os.environ.get('REDIS_PASSWORD'),
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SSL': True,
            'SSL_CERT_REQS': 'required',
        },
        'KEY_PREFIX': 'upeu_ppp',
        'TIMEOUT': 300,
    }
}

# Sesiones en Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ============================================================================
# CELERY - Azure Cache for Redis (broker)
# ============================================================================

CELERY_BROKER_URL = os.environ.get('REDIS_URL')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL')
CELERY_BROKER_USE_SSL = {
    'ssl_cert_reqs': 'required'
}
CELERY_REDIS_BACKEND_USE_SSL = {
    'ssl_cert_reqs': 'required'
}

# ============================================================================
# ARCHIVOS ESTÁTICOS Y MEDIA - Azure Blob Storage
# ============================================================================

# Azure Storage Account
AZURE_ACCOUNT_NAME = os.environ.get('AZURE_STORAGE_ACCOUNT_NAME')
AZURE_ACCOUNT_KEY = os.environ.get('AZURE_STORAGE_ACCOUNT_KEY')
AZURE_CONTAINER_STATIC = os.environ.get('AZURE_CONTAINER_STATIC', 'static')
AZURE_CONTAINER_MEDIA = os.environ.get('AZURE_CONTAINER_MEDIA', 'media')
AZURE_CUSTOM_DOMAIN = f'{AZURE_ACCOUNT_NAME}.blob.core.windows.net'

# Static files (CSS, JavaScript, Images)
STATICFILES_STORAGE = 'storages.backends.azure_storage.AzureStorage'
AZURE_LOCATION = AZURE_CONTAINER_STATIC
STATIC_URL = f'https://{AZURE_CUSTOM_DOMAIN}/{AZURE_CONTAINER_STATIC}/'

# Media files (user uploads)
DEFAULT_FILE_STORAGE = 'config.azure_storage.AzureMediaStorage'
MEDIA_URL = f'https://{AZURE_CUSTOM_DOMAIN}/{AZURE_CONTAINER_MEDIA}/'

# ============================================================================
# LOGGING - Azure Application Insights
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['mail_admins', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'src': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING = os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING')

if APPLICATIONINSIGHTS_CONNECTION_STRING:
    MIDDLEWARE += [
        'applicationinsights.django.ApplicationInsightsMiddleware',
    ]
    
    INSTALLED_APPS += [
        'applicationinsights.django',
    ]

# ============================================================================
# EMAIL - Azure Communication Services o SendGrid
# ============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.sendgrid.net')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@upeu.edu.pe')

# ============================================================================
# CORS - Configuración para dominios específicos
# ============================================================================

CORS_ALLOWED_ORIGINS = [
    origin.strip() 
    for origin in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
    if origin.strip()
]

CORS_ALLOW_CREDENTIALS = True

# ============================================================================
# SEGURIDAD ADICIONAL
# ============================================================================

# Protección contra clickjacking
X_FRAME_OPTIONS = 'DENY'

# Protección XSS
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "cdn.jsdelivr.net")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "cdn.jsdelivr.net")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "data:", "cdn.jsdelivr.net")

# ============================================================================
# PERFORMANCE
# ============================================================================

# WhiteNoise para servir static files (backup)
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Compresión GZip
MIDDLEWARE.insert(0, 'django.middleware.gzip.GZipMiddleware')

# ============================================================================
# MONITORING
# ============================================================================

# Sentry (opcional)
SENTRY_DSN = os.environ.get('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment='production',
    )
```

---

### **2. Archivo `config/azure_storage.py`**

Storage backend personalizado para Azure:

```python
"""
azure_storage.py - Azure Blob Storage backends
"""
from storages.backends.azure_storage import AzureStorage


class AzureMediaStorage(AzureStorage):
    """Storage para archivos media (uploads de usuarios)."""
    
    account_name = settings.AZURE_ACCOUNT_NAME
    account_key = settings.AZURE_ACCOUNT_KEY
    azure_container = settings.AZURE_CONTAINER_MEDIA
    expiration_secs = None
    overwrite_files = False  # No sobrescribir archivos existentes
    

class AzureStaticStorage(AzureStorage):
    """Storage para archivos estáticos (CSS, JS, etc)."""
    
    account_name = settings.AZURE_ACCOUNT_NAME
    account_key = settings.AZURE_ACCOUNT_KEY
    azure_container = settings.AZURE_CONTAINER_STATIC
    expiration_secs = None
```

---

### **3. Variables de Entorno en Azure App Service**

Configurar en el portal de Azure:

```bash
# Django
DEBUG=False
SECRET_KEY=<random-secure-key>
ALLOWED_HOSTS=app-upeu-ppp-prod.azurewebsites.net,upeu-practicas.edu.pe
DJANGO_SETTINGS_MODULE=config.settings_azure

# Database
DB_HOST=psql-upeu-ppp-prod.postgres.database.azure.com
DB_NAME=upeu_ppp_system
DB_USER=upeu_admin
DB_PASSWORD=<secure-password>
DB_PORT=5432

# Redis
REDIS_URL=rediss://redis-upeu-ppp-prod.redis.cache.windows.net:6380
REDIS_PASSWORD=<redis-access-key>
USE_REDIS_CACHE=True

# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=stupeuppprod
AZURE_STORAGE_ACCOUNT_KEY=<storage-access-key>
AZURE_CONTAINER_STATIC=static
AZURE_CONTAINER_MEDIA=media

# Email (SendGrid)
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=<sendgrid-api-key>
DEFAULT_FROM_EMAIL=noreply@upeu.edu.pe

# Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=<key>;IngestionEndpoint=https://...

# CORS
CORS_ALLOWED_ORIGINS=https://upeu-practicas.edu.pe,https://www.upeu-practicas.edu.pe

# JWT
JWT_SECRET_KEY=<jwt-secret-key>
JWT_ACCESS_TOKEN_LIFETIME=15
JWT_REFRESH_TOKEN_LIFETIME=7

# Cloudflare Turnstile
CLOUDFLARE_TURNSTILE_ENABLED=True
CLOUDFLARE_TURNSTILE_SITE_KEY=<site-key>
CLOUDFLARE_TURNSTILE_SECRET_KEY=<secret-key>

# Sentry (opcional)
SENTRY_DSN=https://<key>@<organization>.ingest.sentry.io/<project>
```

---

### **4. Startup Command en Azure App Service**

En **Configuration > General settings > Startup Command**:

```bash
gunicorn config.wsgi:application \
  --bind=0.0.0.0:8000 \
  --workers=4 \
  --threads=2 \
  --timeout=120 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

**Cálculo de workers**:
```
Workers = (2 x CPU cores) + 1
Ejemplo: (2 x 2) + 1 = 5 workers
```

---

### **5. Requirements para Producción**

Actualizar `requirements/production.txt`:

```txt
-r base.txt

# Production server
gunicorn==22.0.0
whitenoise==6.7.0

# Azure specific
django-storages[azure]==1.14.2
azure-storage-blob==12.19.0
applicationinsights==0.11.10

# Monitoring
sentry-sdk==1.40.0

# Performance
django-cachalot==2.6.3
django-redis==5.4.0

# Security
django-csp==3.8
django-cors-headers==4.3.1
```

---

### **6. Archivo `.deployment`**

Para Azure deployment configuration:

```ini
[config]
SCM_DO_BUILD_DURING_DEPLOYMENT=true
POST_BUILD_SCRIPT_PATH=deploy.sh
```

---

### **7. Archivo `deploy.sh`**

Script de despliegue automático:

```bash
#!/bin/bash
set -e

echo "=== Starting deployment ==="

# Instalar dependencias
echo "Installing dependencies..."
pip install -r requirements/production.txt

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --settings=config.settings_azure

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput --settings=config.settings_azure

# Create cache table (si usas database cache)
# python manage.py createcachetable --settings=config.settings_azure

# Compilar archivos de traducción (si usas i18n)
# python manage.py compilemessages --settings=config.settings_azure

echo "=== Deployment completed successfully ==="
```

---

### **8. Health Check Endpoint**

Crear endpoint para Azure health monitoring:

```python
# src/adapters/primary/rest_api/health.py

from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis


def health_check(request):
    """Health check endpoint para Azure."""
    
    health_status = {
        'status': 'healthy',
        'checks': {}
    }
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Check Redis
    try:
        cache.set('health_check', 'ok', 10)
        result = cache.get('health_check')
        health_status['checks']['cache'] = 'healthy' if result == 'ok' else 'unhealthy'
    except Exception as e:
        health_status['checks']['cache'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return JsonResponse(health_status, status=status_code)
```

Agregar a `config/urls.py`:

```python
from src.adapters.primary.rest_api.health import health_check

urlpatterns = [
    path('health/', health_check, name='health-check'),
    # ... otras URLs
]
```

---

### **9. Configuración de Auto-scaling**

Reglas recomendadas:

```yaml
Scale Out (aumentar instancias):
  - CPU > 70% por 5 minutos → +1 instancia
  - Memory > 80% por 5 minutos → +1 instancia
  - Request count > 1000/min → +1 instancia
  
Scale In (disminuir instancias):
  - CPU < 30% por 10 minutos → -1 instancia
  - Memory < 50% por 10 minutos → -1 instancia

Limits:
  - Minimum instances: 2
  - Maximum instances: 5
  - Cooldown: 5 minutos
```

---

### **10. Backup Strategy**

Script de backup automático:

```bash
#!/bin/bash
# backup_azure.sh

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/backups/azure"

# Backup PostgreSQL
az postgres flexible-server backup create \
  --resource-group rg-upeu-ppp-prod \
  --name psql-upeu-ppp-prod \
  --backup-name "backup_${TIMESTAMP}"

# Backup Blob Storage (media files)
az storage blob download-batch \
  --account-name stupeuppprod \
  --source media \
  --destination "${BACKUP_DIR}/media_${TIMESTAMP}" \
  --pattern "*"

# Backup Redis (export RDB)
az redis export \
  --resource-group rg-upeu-ppp-prod \
  --name redis-upeu-ppp-prod \
  --prefix "backup_${TIMESTAMP}" \
  --container backups \
  --file-format RDB

echo "Backup completed: ${TIMESTAMP}"
```

Configurar como Azure Function o Logic App para ejecución diaria.

---

### **11. Disaster Recovery Plan**

```yaml
Recovery Procedures:

1. Database Corruption:
   - Restore from automated backup
   - Point-in-time restore available (últimos 35 días)
   - Time to restore: ~15-30 minutos

2. Application Failure:
   - Swap deployment slots (staging → production)
   - Rollback to previous container image
   - Time to restore: ~2-5 minutos

3. Regional Outage:
   - Failover to secondary region (si geo-replication habilitado)
   - Update DNS to point to backup region
   - Time to restore: ~30-60 minutos

4. Data Loss:
   - Restore from geo-redundant backup
   - Replay transaction logs
   - Time to restore: ~1-2 horas
```

---

### **12. Performance Optimization**

```python
# config/settings_azure.py

# Database connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 600
DATABASES['default']['OPTIONS']['connect_timeout'] = 10

# Query optimization
DATABASES['default']['OPTIONS']['options'] = '-c statement_timeout=30000'  # 30 segundos

# Cache configuration
CACHES['default']['TIMEOUT'] = 300  # 5 minutos default
CACHES['default']['OPTIONS']['MAX_ENTRIES'] = 10000

# Static files compression
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_COMPRESS_OFFLINE = True

# Middleware optimization
MIDDLEWARE_CLASSES = [
    'django.middleware.cache.UpdateCacheMiddleware',  # Cache pages
    # ... otros middleware
    'django.middleware.cache.FetchFromCacheMiddleware',
]

CACHE_MIDDLEWARE_SECONDS = 600
```

---

**¿Quieres que genere los archivos de Terraform/Bicep para automatizar todo el despliegue?** 🚀
