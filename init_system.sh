#!/bin/bash

# =======================================================
# SCRIPT DE INICIALIZACIÓN COMPLETA - SISTEMA PPP UPeU
# Orquesta la inicialización de toda la infraestructura
# =======================================================

set -e  # Detener en cualquier error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =======================================================
# VERIFICACIONES PREVIAS
# =======================================================

log "Iniciando verificaciones previas..."

# Verificar Docker
if ! command -v docker &> /dev/null; then
    error "Docker no está instalado. Por favor instalar Docker primero."
    exit 1
fi

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose no está instalado. Por favor instalar Docker Compose primero."
    exit 1
fi

# Verificar archivos necesarios
required_files=(
    "docker-compose.yml"
    "docs/arquitectura/database_schema.sql"
    "docs/arquitectura/seguridad_tablas.sql"
    "docs/arquitectura/mongodb_init.js"
    "requirements/base.txt"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        error "Archivo requerido no encontrado: $file"
        exit 1
    fi
done

success "Verificaciones previas completadas"

# =======================================================
# CONFIGURACIÓN DE VARIABLES DE ENTORNO
# =======================================================

log "Configurando variables de entorno..."

# Crear archivo .env si no existe
if [ ! -f ".env" ]; then
    cat > .env << EOF
# ==============================================
# CONFIGURACIÓN DE ENTORNO - SISTEMA PPP UPeU
# ==============================================

# Base de datos PostgreSQL
POSTGRES_DB=upeu_ppp_db
POSTGRES_USER=upeu_admin
POSTGRES_PASSWORD=UPeU2024_Secure!
POSTGRES_HOST=postgres_db
POSTGRES_PORT=5432

# MongoDB
MONGO_DB=upeu_documents
MONGO_USER=django_app
MONGO_PASSWORD=django_mongo_secure_2024
MONGO_HOST=mongodb
MONGO_PORT=27017

# Redis
REDIS_HOST=redis_cache
REDIS_PORT=6379
REDIS_PASSWORD=Redis_UPeU_2024!
REDIS_DB=0

# Django
SECRET_KEY=django-insecure-$(openssl rand -base64 32)
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DJANGO_SETTINGS_MODULE=config.settings

# Celery
CELERY_BROKER_URL=redis://:Redis_UPeU_2024!@redis_cache:6379/1
CELERY_RESULT_BACKEND=redis://:Redis_UPeU_2024!@redis_cache:6379/2

# JWT
JWT_SECRET_KEY=$(openssl rand -base64 64)
JWT_ACCESS_TOKEN_LIFETIME=15
JWT_REFRESH_TOKEN_LIFETIME=7

# GraphQL
GRAPHQL_INTROSPECTION=True
GRAPHQL_PLAYGROUND=True
GRAPHQL_MAX_QUERY_DEPTH=10
GRAPHQL_MAX_QUERY_COMPLEXITY=1000

# Seguridad
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
BLACKLIST_THRESHOLD=10
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Archivos y Media
MAX_UPLOAD_SIZE=52428800
MEDIA_URL=/media/
STATIC_URL=/static/

# Email (configurar según proveedor)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Logging
LOG_LEVEL=INFO
LOG_TO_FILE=True
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# Monitoreo
ENABLE_METRICS=True
METRICS_RETENTION_DAYS=90

# Entorno
ENVIRONMENT=development
EOF
    success "Archivo .env creado"
else
    warning "Archivo .env ya existe, no se sobrescribió"
fi

# =======================================================
# CONSTRUCCIÓN DE IMÁGENES DOCKER
# =======================================================

log "Construyendo imágenes Docker..."

# Limpiar imágenes anteriores si existen
docker-compose down -v --remove-orphans 2>/dev/null || true

# Construir imagen de la aplicación
docker-compose build django_app

success "Imágenes Docker construidas"

# =======================================================
# INICIALIZACIÓN DE SERVICIOS BASE
# =======================================================

log "Iniciando servicios de base de datos..."

# Iniciar solo los servicios de base de datos primero
docker-compose up -d postgres_db mongodb redis_cache

# Esperar a que PostgreSQL esté listo
log "Esperando a que PostgreSQL esté listo..."
until docker-compose exec postgres_db pg_isready -U upeu_admin -d upeu_ppp_db; do
    echo "PostgreSQL no está listo aún..."
    sleep 2
done
success "PostgreSQL está listo"

# Esperar a que MongoDB esté listo
log "Esperando a que MongoDB esté listo..."
until docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')" >/dev/null 2>&1; do
    echo "MongoDB no está listo aún..."
    sleep 2
done
success "MongoDB está listo"

# Esperar a que Redis esté listo
log "Esperando a que Redis esté listo..."
until docker-compose exec redis_cache redis-cli ping >/dev/null 2>&1; do
    echo "Redis no está listo aún..."
    sleep 2
done
success "Redis está listo"

# =======================================================
# INICIALIZACIÓN DE POSTGRESQL
# =======================================================

log "Inicializando esquema de PostgreSQL..."

# Crear esquema principal
docker-compose exec -T postgres_db psql -U upeu_admin -d upeu_ppp_db < docs/arquitectura/database_schema.sql

# Crear tablas de seguridad
docker-compose exec -T postgres_db psql -U upeu_admin -d upeu_ppp_db < docs/arquitectura/seguridad_tablas.sql

# Verificar instalación de PostgreSQL
TABLES_COUNT=$(docker-compose exec postgres_db psql -U upeu_admin -d upeu_ppp_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
success "PostgreSQL inicializado: $TABLES_COUNT tablas creadas"

# =======================================================
# INICIALIZACIÓN DE MONGODB
# =======================================================

log "Inicializando MongoDB..."

# Ejecutar script de inicialización
docker-compose exec -T mongodb mongosh upeu_documents < docs/arquitectura/mongodb_init.js

# Verificar instalación de MongoDB
COLLECTIONS_COUNT=$(docker-compose exec mongodb mongosh upeu_documents --eval "db.getCollectionNames().length" --quiet)
success "MongoDB inicializado: $COLLECTIONS_COUNT colecciones creadas"

# =======================================================
# INICIALIZACIÓN DE REDIS
# =======================================================

log "Configurando Redis..."

# Configurar Redis con configuraciones básicas
docker-compose exec redis_cache redis-cli CONFIG SET maxmemory 256mb
docker-compose exec redis_cache redis-cli CONFIG SET maxmemory-policy allkeys-lru
docker-compose exec redis_cache redis-cli CONFIG SET save "900 1 300 10 60 10000"

success "Redis configurado"

# =======================================================
# INICIALIZACIÓN DE LA APLICACIÓN DJANGO
# =======================================================

log "Inicializando aplicación Django..."

# Iniciar aplicación Django
docker-compose up -d django_app

# Esperar a que Django esté listo
log "Esperando a que Django esté listo..."
until docker-compose exec django_app python manage.py check; do
    echo "Django no está listo aún..."
    sleep 3
done

# Ejecutar migraciones
log "Ejecutando migraciones de Django..."
docker-compose exec django_app python manage.py makemigrations
docker-compose exec django_app python manage.py migrate

# Crear superusuario
log "Creando superusuario..."
docker-compose exec django_app python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@upeu.edu.pe', 'UPeU2024Admin!')
    print('Superusuario creado: admin / UPeU2024Admin!')
else:
    print('Superusuario ya existe')
EOF

# Cargar datos iniciales si existen
if [ -f "fixtures/initial_data.json" ]; then
    log "Cargando datos iniciales..."
    docker-compose exec django_app python manage.py loaddata fixtures/initial_data.json
fi

success "Django inicializado"

# =======================================================
# INICIALIZACIÓN DE CELERY
# =======================================================

log "Iniciando workers de Celery..."

# Iniciar Celery worker y beat
docker-compose up -d celery_worker celery_beat

# Verificar que Celery esté funcionando
sleep 5
if docker-compose ps celery_worker | grep -q "Up"; then
    success "Celery worker iniciado"
else
    warning "Problema al iniciar Celery worker"
fi

# =======================================================
# VERIFICACIONES FINALES
# =======================================================

log "Realizando verificaciones finales..."

# Verificar que todos los servicios estén corriendo
services=("postgres_db" "mongodb" "redis_cache" "django_app" "celery_worker" "celery_beat")
all_running=true

for service in "${services[@]}"; do
    if docker-compose ps "$service" | grep -q "Up"; then
        success "✓ $service está corriendo"
    else
        error "✗ $service no está corriendo"
        all_running=false
    fi
done

# Verificar conectividad de la aplicación
log "Verificando conectividad de la aplicación..."
if curl -f http://localhost:8000/health/ >/dev/null 2>&1; then
    success "✓ Aplicación web responde correctamente"
else
    warning "✗ Aplicación web no responde (puede necesitar más tiempo)"
fi

# Verificar GraphQL endpoint
if curl -f http://localhost:8000/graphql/ >/dev/null 2>&1; then
    success "✓ GraphQL endpoint disponible"
else
    warning "✗ GraphQL endpoint no disponible"
fi

# =======================================================
# INFORMACIÓN FINAL
# =======================================================

echo ""
echo "======================================================="
echo -e "${GREEN}SISTEMA PPP UPeU INICIALIZADO EXITOSAMENTE${NC}"
echo "======================================================="
echo ""
echo "🌐 URLs disponibles:"
echo "   • Aplicación web: http://localhost:8000"
echo "   • Admin Django: http://localhost:8000/admin"
echo "   • GraphQL Playground: http://localhost:8000/graphql"
echo "   • API REST: http://localhost:8000/api/v1/"
echo ""
echo "🔐 Credenciales:"
echo "   • Superusuario Django: admin / UPeU2024Admin!"
echo "   • PostgreSQL: upeu_admin / UPeU2024_Secure!"
echo "   • MongoDB: django_app / django_mongo_secure_2024"
echo ""
echo "🐳 Servicios Docker corriendo:"
docker-compose ps
echo ""
echo "📊 Estado de las bases de datos:"
echo "   • PostgreSQL: $TABLES_COUNT tablas"
echo "   • MongoDB: $COLLECTIONS_COUNT colecciones"
echo "   • Redis: Configurado y listo"
echo ""
echo "📝 Comandos útiles:"
echo "   • Ver logs: docker-compose logs -f [servicio]"
echo "   • Reiniciar: docker-compose restart [servicio]"
echo "   • Detener todo: docker-compose down"
echo "   • Backup DB: docker-compose exec postgres_db pg_dump -U upeu_admin upeu_ppp_db > backup.sql"
echo ""

if [ "$all_running" = true ]; then
    echo -e "${GREEN}✅ Todos los servicios están funcionando correctamente${NC}"
    echo "El sistema está listo para desarrollo y testing."
else
    echo -e "${YELLOW}⚠️  Algunos servicios pueden necesitar atención${NC}"
    echo "Revisar logs con: docker-compose logs"
fi

echo ""
echo "======================================================="