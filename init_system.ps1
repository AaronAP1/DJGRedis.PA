# =======================================================
# SCRIPT DE INICIALIZACIÓN COMPLETA - SISTEMA PPP UPeU
# Versión PowerShell para Windows
# =======================================================

param(
    [switch]$SkipVerification = $false,
    [switch]$CleanStart = $false
)

# Configuración de colores
$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] " -ForegroundColor Blue -NoNewline
    Write-Host $Message
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] " -ForegroundColor Yellow -NoNewline
    Write-Host $Message
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
    Write-Host $Message
}

# =======================================================
# VERIFICACIONES PREVIAS
# =======================================================

if (-not $SkipVerification) {
    Write-Log "Iniciando verificaciones previas..."

    # Verificar Docker
    try {
        docker --version | Out-Null
        Write-Success "Docker encontrado"
    }
    catch {
        Write-Error "Docker no está instalado o no está en PATH"
        exit 1
    }

    # Verificar Docker Compose
    try {
        docker-compose --version | Out-Null
        Write-Success "Docker Compose encontrado"
    }
    catch {
        Write-Error "Docker Compose no está instalado o no está en PATH"
        exit 1
    }

    # Verificar archivos necesarios
    $requiredFiles = @(
        "docker-compose.yml",
        "docs\arquitectura\database_schema.sql",
        "docs\arquitectura\seguridad_tablas.sql",
        "docs\arquitectura\mongodb_init.js",
        "requirements\base.txt"
    )

    foreach ($file in $requiredFiles) {
        if (-not (Test-Path $file)) {
            Write-Error "Archivo requerido no encontrado: $file"
            exit 1
        }
    }

    Write-Success "Verificaciones previas completadas"
}

# =======================================================
# CONFIGURACIÓN DE VARIABLES DE ENTORNO
# =======================================================

Write-Log "Configurando variables de entorno..."

if (-not (Test-Path ".env")) {
    $envContent = @"
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
SECRET_KEY=django-insecure-$([System.Web.Security.Membership]::GeneratePassword(50, 0))
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DJANGO_SETTINGS_MODULE=config.settings

# Celery
CELERY_BROKER_URL=redis://:Redis_UPeU_2024!@redis_cache:6379/1
CELERY_RESULT_BACKEND=redis://:Redis_UPeU_2024!@redis_cache:6379/2

# JWT
JWT_SECRET_KEY=$([System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes([System.Web.Security.Membership]::GeneratePassword(64, 0))))
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
"@
    
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Success "Archivo .env creado"
} else {
    Write-Warning "Archivo .env ya existe, no se sobrescribió"
}

# =======================================================
# LIMPIEZA INICIAL (SI SE SOLICITA)
# =======================================================

if ($CleanStart) {
    Write-Log "Realizando limpieza inicial..."
    try {
        docker-compose down -v --remove-orphans 2>$null
        Write-Success "Limpieza completada"
    }
    catch {
        Write-Warning "No había servicios previos para limpiar"
    }
}

# =======================================================
# CONSTRUCCIÓN DE IMÁGENES DOCKER
# =======================================================

Write-Log "Construyendo imágenes Docker..."

try {
    docker-compose build django_app
    Write-Success "Imágenes Docker construidas"
}
catch {
    Write-Error "Error al construir imágenes Docker"
    exit 1
}

# =======================================================
# INICIALIZACIÓN DE SERVICIOS BASE
# =======================================================

Write-Log "Iniciando servicios de base de datos..."

# Iniciar solo los servicios de base de datos primero
docker-compose up -d postgres_db mongodb redis_cache

# Función para esperar a que un servicio esté listo
function Wait-ForService {
    param(
        [string]$ServiceName,
        [scriptblock]$TestCommand,
        [int]$MaxAttempts = 30
    )
    
    Write-Log "Esperando a que $ServiceName esté listo..."
    $attempts = 0
    
    do {
        $attempts++
        try {
            $result = & $TestCommand
            if ($result) {
                Write-Success "$ServiceName está listo"
                return $true
            }
        }
        catch {
            # Continuar intentando
        }
        
        if ($attempts -lt $MaxAttempts) {
            Write-Host "  $ServiceName no está listo aún... (intento $attempts/$MaxAttempts)"
            Start-Sleep -Seconds 2
        }
    } while ($attempts -lt $MaxAttempts)
    
    Write-Error "$ServiceName no respondió después de $MaxAttempts intentos"
    return $false
}

# Esperar a PostgreSQL
$pgReady = Wait-ForService "PostgreSQL" {
    $result = docker-compose exec postgres_db pg_isready -U upeu_admin -d upeu_ppp_db 2>$null
    return $LASTEXITCODE -eq 0
}

# Esperar a MongoDB
$mongoReady = Wait-ForService "MongoDB" {
    $result = docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')" 2>$null
    return $LASTEXITCODE -eq 0
}

# Esperar a Redis
$redisReady = Wait-ForService "Redis" {
    $result = docker-compose exec redis_cache redis-cli ping 2>$null
    return $LASTEXITCODE -eq 0
}

if (-not ($pgReady -and $mongoReady -and $redisReady)) {
    Write-Error "No todos los servicios de base de datos están listos"
    exit 1
}

# =======================================================
# INICIALIZACIÓN DE POSTGRESQL
# =======================================================

Write-Log "Inicializando esquema de PostgreSQL..."

try {
    # Crear esquema principal
    Get-Content "docs\arquitectura\database_schema.sql" | docker-compose exec -T postgres_db psql -U upeu_admin -d upeu_ppp_db
    
    # Crear tablas de seguridad
    Get-Content "docs\arquitectura\seguridad_tablas.sql" | docker-compose exec -T postgres_db psql -U upeu_admin -d upeu_ppp_db
    
    # Verificar instalación
    $tablesCount = docker-compose exec postgres_db psql -U upeu_admin -d upeu_ppp_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
    Write-Success "PostgreSQL inicializado: $($tablesCount.Trim()) tablas creadas"
}
catch {
    Write-Error "Error al inicializar PostgreSQL: $_"
    exit 1
}

# =======================================================
# INICIALIZACIÓN DE MONGODB
# =======================================================

Write-Log "Inicializando MongoDB..."

try {
    Get-Content "docs\arquitectura\mongodb_init.js" | docker-compose exec -T mongodb mongosh upeu_documents
    
    $collectionsCount = docker-compose exec mongodb mongosh upeu_documents --eval "db.getCollectionNames().length" --quiet
    Write-Success "MongoDB inicializado: $($collectionsCount.Trim()) colecciones creadas"
}
catch {
    Write-Error "Error al inicializar MongoDB: $_"
    exit 1
}

# =======================================================
# CONFIGURACIÓN DE REDIS
# =======================================================

Write-Log "Configurando Redis..."

try {
    docker-compose exec redis_cache redis-cli CONFIG SET maxmemory 256mb
    docker-compose exec redis_cache redis-cli CONFIG SET maxmemory-policy allkeys-lru
    docker-compose exec redis_cache redis-cli CONFIG SET save "900 1 300 10 60 10000"
    Write-Success "Redis configurado"
}
catch {
    Write-Warning "Error al configurar Redis, pero el servicio puede funcionar"
}

# =======================================================
# INICIALIZACIÓN DE DJANGO
# =======================================================

Write-Log "Inicializando aplicación Django..."

# Iniciar aplicación Django
docker-compose up -d django_app

# Esperar a que Django esté listo
$djangoReady = Wait-ForService "Django" {
    $result = docker-compose exec django_app python manage.py check 2>$null
    return $LASTEXITCODE -eq 0
}

if (-not $djangoReady) {
    Write-Error "Django no se pudo inicializar correctamente"
    exit 1
}

# Ejecutar migraciones
Write-Log "Ejecutando migraciones de Django..."
try {
    docker-compose exec django_app python manage.py makemigrations
    docker-compose exec django_app python manage.py migrate
    Write-Success "Migraciones completadas"
}
catch {
    Write-Error "Error en migraciones de Django"
    exit 1
}

# Crear superusuario
Write-Log "Creando superusuario..."
$createSuperuserScript = @"
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@upeu.edu.pe', 'UPeU2024Admin!')
    print('Superusuario creado: admin / UPeU2024Admin!')
else:
    print('Superusuario ya existe')
"@

$createSuperuserScript | docker-compose exec -T django_app python manage.py shell

# Cargar datos iniciales si existen
if (Test-Path "fixtures\initial_data.json") {
    Write-Log "Cargando datos iniciales..."
    docker-compose exec django_app python manage.py loaddata fixtures/initial_data.json
}

Write-Success "Django inicializado"

# =======================================================
# INICIALIZACIÓN DE CELERY
# =======================================================

Write-Log "Iniciando workers de Celery..."

docker-compose up -d celery_worker celery_beat

Start-Sleep -Seconds 5

$celeryStatus = docker-compose ps celery_worker
if ($celeryStatus -match "Up") {
    Write-Success "Celery worker iniciado"
} else {
    Write-Warning "Problema al iniciar Celery worker"
}

# =======================================================
# VERIFICACIONES FINALES
# =======================================================

Write-Log "Realizando verificaciones finales..."

$services = @("postgres_db", "mongodb", "redis_cache", "django_app", "celery_worker", "celery_beat")
$allRunning = $true

foreach ($service in $services) {
    $status = docker-compose ps $service
    if ($status -match "Up") {
        Write-Success "✓ $service está corriendo"
    } else {
        Write-Error "✗ $service no está corriendo"
        $allRunning = $false
    }
}

# Verificar conectividad de la aplicación
Write-Log "Verificando conectividad de la aplicación..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health/" -TimeoutSec 10 -ErrorAction Stop
    Write-Success "✓ Aplicación web responde correctamente"
}
catch {
    Write-Warning "✗ Aplicación web no responde (puede necesitar más tiempo)"
}

# Verificar GraphQL endpoint
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/graphql/" -TimeoutSec 10 -ErrorAction Stop
    Write-Success "✓ GraphQL endpoint disponible"
}
catch {
    Write-Warning "✗ GraphQL endpoint no disponible"
}

# =======================================================
# INFORMACIÓN FINAL
# =======================================================

Write-Host ""
Write-Host "=======================================================" -ForegroundColor Green
Write-Host "SISTEMA PPP UPeU INICIALIZADO EXITOSAMENTE" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 URLs disponibles:"
Write-Host "   • Aplicación web: http://localhost:8000"
Write-Host "   • Admin Django: http://localhost:8000/admin"
Write-Host "   • GraphQL Playground: http://localhost:8000/graphql"
Write-Host "   • API REST: http://localhost:8000/api/v1/"
Write-Host ""
Write-Host "🔐 Credenciales:"
Write-Host "   • Superusuario Django: admin / UPeU2024Admin!"
Write-Host "   • PostgreSQL: upeu_admin / UPeU2024_Secure!"
Write-Host "   • MongoDB: django_app / django_mongo_secure_2024"
Write-Host ""
Write-Host "🐳 Servicios Docker corriendo:"
docker-compose ps
Write-Host ""
Write-Host "📝 Comandos útiles:"
Write-Host "   • Ver logs: docker-compose logs -f [servicio]"
Write-Host "   • Reiniciar: docker-compose restart [servicio]"
Write-Host "   • Detener todo: docker-compose down"
Write-Host "   • Backup DB: docker-compose exec postgres_db pg_dump -U upeu_admin upeu_ppp_db > backup.sql"
Write-Host ""

if ($allRunning) {
    Write-Host "✅ Todos los servicios están funcionando correctamente" -ForegroundColor Green
    Write-Host "El sistema está listo para desarrollo y testing."
} else {
    Write-Host "⚠️  Algunos servicios pueden necesitar atención" -ForegroundColor Yellow
    Write-Host "Revisar logs con: docker-compose logs"
}

Write-Host ""
Write-Host "======================================================="

# Pausar para mostrar resultados
Write-Host ""
Write-Host "Presiona cualquier tecla para continuar..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")