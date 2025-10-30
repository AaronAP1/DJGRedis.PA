# =====================================================
# AZURE DATABASES ONLY DEPLOYMENT - PowerShell
# Sistema de Gestión de Prácticas Profesionales - UPeU
# =====================================================
# Este script despliega SOLO las bases de datos en Azure
# Ideal para usar con Azure for Students ($100/mes crédito)

param(
    [string]$ResourceGroup = "rg-upeu-ppp-databases",
    [string]$Location = "eastus",
    [string]$PostgresServer = "psql-upeu-ppp",
    [string]$PostgresDb = "upeu_ppp_system",
    [string]$PostgresAdmin = "upeu_admin",
    [string]$RedisName = "redis-upeu-ppp",
    [string]$CosmosAccount = "cosmos-upeu-ppp",
    [string]$KeyVaultName = "kv-upeu-ppp-db"
)

$ErrorActionPreference = "Stop"

# =====================================================
# BANNER
# =====================================================
Clear-Host
Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  AZURE DATABASES DEPLOYMENT - UPeU PPP System" -ForegroundColor Cyan
Write-Host "  Desplegando: PostgreSQL + Redis + Cosmos DB" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# =====================================================
# CHECK PREREQUISITES
# =====================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verificando Prerrequisitos" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check Azure CLI
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Host "[OK] Azure CLI instalado: $($azVersion.'azure-cli')" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Azure CLI no esta instalado" -ForegroundColor Red
    Write-Host "`nInstalar desde: https://aka.ms/installazurecliwindows" -ForegroundColor Yellow
    exit 1
}

# Check login
try {
    $account = az account show --output json | ConvertFrom-Json
    Write-Host "[OK] Autenticacion verificada" -ForegroundColor Green
    
    Write-Host "`nInformacion de la cuenta:" -ForegroundColor Cyan
    Write-Host "  Nombre: $($account.name)"
    Write-Host "  ID: $($account.id)"
    Write-Host "  Usuario: $($account.user.name)"
    
    # Check if Azure for Students
    if ($account.name -like "*Azure for Students*") {
        Write-Host "`n[STUDENTS] Cuenta Azure for Students detectada - `$100 USD/mes de credito!" -ForegroundColor Green
    }
} catch {
    Write-Host "[WARN] No estas autenticado en Azure" -ForegroundColor Yellow
    Write-Host "Iniciando login..." -ForegroundColor Cyan
    az login
    $account = az account show --output json | ConvertFrom-Json
}

# =====================================================
# SHOW COSTS
# =====================================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Costos Estimados Mensuales" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nConfiguracion optimizada para Students:" -ForegroundColor White
Write-Host ""
Write-Host "1. PostgreSQL Flexible Server (Burstable B1ms)" -ForegroundColor Cyan
Write-Host "   - 1 vCore, 2GB RAM, 32GB Storage"
Write-Host "   Costo: ~`$12-15/mes" -ForegroundColor Green
Write-Host ""
Write-Host "2. Redis Cache (Basic C0)" -ForegroundColor Cyan
Write-Host "   - 250MB Memoria"
Write-Host "   Costo: ~`$16/mes" -ForegroundColor Green
Write-Host ""
Write-Host "3. Cosmos DB Serverless (MongoDB API)" -ForegroundColor Cyan
Write-Host "   - Pay-per-use"
Write-Host "   Costo: ~`$5-10/mes (uso moderado)" -ForegroundColor Green
Write-Host ""
Write-Host "4. Key Vault" -ForegroundColor Cyan
Write-Host "   Costo: ~`$0.03/mes" -ForegroundColor Green
Write-Host ""
Write-Host "TOTAL ESTIMADO: ~`$35-45/mes" -ForegroundColor Green
Write-Host "Con Azure for Students: GRATIS (`$100 credito/mes)" -ForegroundColor Blue

$continue = Read-Host "`nContinuar con el deployment? (Y/N)"
if ($continue -ne 'Y' -and $continue -ne 'y') {
    Write-Host "Deployment cancelado" -ForegroundColor Yellow
    exit 0
}

# =====================================================
# CREATE RESOURCE GROUP
# =====================================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Creando Resource Group" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$rgExists = az group exists --name $ResourceGroup
if ($rgExists -eq 'true') {
    Write-Host "[WARN] Resource group '$ResourceGroup' ya existe" -ForegroundColor Yellow
} else {
    Write-Host "Creando resource group en $Location..." -ForegroundColor Cyan
    az group create --name $ResourceGroup --location $Location --output none
    Write-Host "[OK] Resource group creado: $ResourceGroup" -ForegroundColor Green
}

# =====================================================
# CREATE KEY VAULT
# =====================================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Creando Key Vault" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

try {
    az keyvault show --name $KeyVaultName --resource-group $ResourceGroup --output none 2>$null
    Write-Host "[WARN] Key Vault ya existe" -ForegroundColor Yellow
} catch {
    Write-Host "Creando Key Vault..." -ForegroundColor Cyan
    az keyvault create `
        --name $KeyVaultName `
        --resource-group $ResourceGroup `
        --location $Location `
        --output none
    Write-Host "[OK] Key Vault creado: $KeyVaultName" -ForegroundColor Green
}

# =====================================================
# CREATE POSTGRESQL
# =====================================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Creando PostgreSQL Flexible Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Generate secure password
$PostgresPassword = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 20 | ForEach-Object {[char]$_})

try {
    az postgres flexible-server show `
        --name $PostgresServer `
        --resource-group $ResourceGroup `
        --output none 2>$null
    Write-Host "[WARN] PostgreSQL server ya existe" -ForegroundColor Yellow
    
    # Try to get password from Key Vault
    try {
        $PostgresPassword = az keyvault secret show `
            --vault-name $KeyVaultName `
            --name "postgres-password" `
            --query value -o tsv
    } catch {
        Write-Host "[WARN] No se pudo recuperar la contrasena del Key Vault" -ForegroundColor Yellow
        $PostgresPassword = Read-Host "Ingresa la contrasena de PostgreSQL" -AsSecureString
        $PostgresPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [Runtime.InteropServices.Marshal]::SecureStringToBSTR($PostgresPassword))
    }
} catch {
    Write-Host "Creando PostgreSQL Flexible Server (optimizado para Students)..." -ForegroundColor Cyan
    Write-Host "[WAIT] Esto puede tomar 5-10 minutos, por favor espera..." -ForegroundColor Yellow
    
    az postgres flexible-server create `
        --name $PostgresServer `
        --resource-group $ResourceGroup `
        --location $Location `
        --admin-user $PostgresAdmin `
        --admin-password $PostgresPassword `
        --sku-name Standard_B1ms `
        --tier Burstable `
        --storage-size 32 `
        --version 15 `
        --public-access 0.0.0.0-255.255.255.255 `
        --backup-retention 7 `
        --output none
    
    Write-Host "[OK] PostgreSQL server creado: $PostgresServer" -ForegroundColor Green
    
    # Store password
    az keyvault secret set `
        --vault-name $KeyVaultName `
        --name "postgres-password" `
        --value $PostgresPassword `
        --output none
    
    # Create database
    Write-Host "Creando base de datos '$PostgresDb'..." -ForegroundColor Cyan
    az postgres flexible-server db create `
        --resource-group $ResourceGroup `
        --server-name $PostgresServer `
        --database-name $PostgresDb `
        --output none
    
    Write-Host "✅ Base de datos '$PostgresDb' creada" -ForegroundColor Green
    
    # Configure firewall
    $MyIP = (Invoke-WebRequest -Uri "https://api.ipify.org" -UseBasicParsing).Content
    Write-Host "Configurando firewall para tu IP: $MyIP" -ForegroundColor Cyan
    
    az postgres flexible-server firewall-rule create `
        --resource-group $ResourceGroup `
        --name $PostgresServer `
        --rule-name "AllowMyIP" `
        --start-ip-address $MyIP `
        --end-ip-address $MyIP `
        --output none
    
    Write-Host "✅ Firewall configurado" -ForegroundColor Green
}

# =====================================================
# CREATE REDIS
# =====================================================
Write-Host "`n========================================"  -ForegroundColor Cyan
Write-Host "🔴 Creando Redis Cache" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

try {
    az redis show --name $RedisName --resource-group $ResourceGroup --output none 2>$null
    Write-Host "⚠️  Redis cache ya existe" -ForegroundColor Yellow
} catch {
    Write-Host "Creando Redis cache (Basic C0)..." -ForegroundColor Cyan
    Write-Host "⏳ Esto puede tomar 10-15 minutos, por favor espera..." -ForegroundColor Yellow
    
    az redis create `
        --name $RedisName `
        --resource-group $ResourceGroup `
        --location $Location `
        --sku Basic `
        --vm-size C0 `
        --enable-non-ssl-port false `
        --output none
    
    Write-Host "✅ Redis cache creado: $RedisName" -ForegroundColor Green
}

# Get Redis key
Write-Host "Obteniendo claves de Redis..." -ForegroundColor Cyan
$RedisKey = az redis list-keys `
    --name $RedisName `
    --resource-group $ResourceGroup `
    --query primaryKey -o tsv

az keyvault secret set `
    --vault-name $KeyVaultName `
    --name "redis-key" `
    --value $RedisKey `
    --output none

Write-Host "✅ Claves de Redis guardadas" -ForegroundColor Green

# =====================================================
# CREATE COSMOS DB
# =====================================================
Write-Host "`n========================================"  -ForegroundColor Cyan
Write-Host "🌌 Creando Cosmos DB (MongoDB API)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

try {
    az cosmosdb show --name $CosmosAccount --resource-group $ResourceGroup --output none 2>$null
    Write-Host "⚠️  Cosmos DB ya existe" -ForegroundColor Yellow
} catch {
    Write-Host "Creando Cosmos DB Serverless..." -ForegroundColor Cyan
    Write-Host "⏳ Esto puede tomar 5-10 minutos, por favor espera..." -ForegroundColor Yellow
    
    az cosmosdb create `
        --name $CosmosAccount `
        --resource-group $ResourceGroup `
        --kind MongoDB `
        --server-version 6.0 `
        --default-consistency-level Session `
        --locations regionName=$Location failoverPriority=0 `
        --capabilities EnableServerless `
        --output none
    
    Write-Host "✅ Cosmos DB creado: $CosmosAccount" -ForegroundColor Green
    
    # Create database
    Write-Host "Creando base de datos 'upeu_documents'..." -ForegroundColor Cyan
    az cosmosdb mongodb database create `
        --account-name $CosmosAccount `
        --resource-group $ResourceGroup `
        --name upeu_documents `
        --output none
    
    Write-Host "✅ Base de datos MongoDB creada" -ForegroundColor Green
}

# Get Cosmos connection string
Write-Host "Obteniendo connection string..." -ForegroundColor Cyan
$CosmosConn = az cosmosdb keys list `
    --name $CosmosAccount `
    --resource-group $ResourceGroup `
    --type connection-strings `
    --query "connectionStrings[0].connectionString" -o tsv

az keyvault secret set `
    --vault-name $KeyVaultName `
    --name "cosmos-connection-string" `
    --value $CosmosConn `
    --output none

Write-Host "✅ Connection string guardado" -ForegroundColor Green

# =====================================================
# GENERATE .ENV FILE
# =====================================================
Write-Host "`n========================================"  -ForegroundColor Cyan
Write-Host "📝 Creando archivo .env.azure" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$PostgresHost = "$PostgresServer.postgres.database.azure.com"
$PostgresConn = "postgres://${PostgresAdmin}:${PostgresPassword}@${PostgresHost}:5432/${PostgresDb}?sslmode=require"
$RedisHost = "$RedisName.redis.cache.windows.net"
$RedisConn = "rediss://:${RedisKey}@${RedisHost}:6380/0"

$envContent = @"
# =====================================================
# AZURE DATABASES CONNECTION - AUTO-GENERATED
# =====================================================
# Generado: $(Get-Date)
# Resource Group: $ResourceGroup
# Location: $Location

# =====================================================
# POSTGRESQL
# =====================================================
DB_NAME=$PostgresDb
DB_USER=$PostgresAdmin
DB_PASSWORD=$PostgresPassword
DB_HOST=$PostgresHost
DB_PORT=5432
DATABASE_URL=$PostgresConn

# =====================================================
# REDIS CACHE
# =====================================================
REDIS_HOST=$RedisHost
REDIS_PORT=6380
REDIS_PASSWORD=$RedisKey
USE_REDIS_CACHE=True
REDIS_URL=$RedisConn

# =====================================================
# MONGODB (Cosmos DB)
# =====================================================
MONGODB_DB_NAME=upeu_documents
MONGODB_URI=$CosmosConn

# =====================================================
# CELERY
# =====================================================
CELERY_BROKER_URL=$RedisConn
CELERY_RESULT_BACKEND=$RedisConn
CELERY_TASK_ALWAYS_EAGER=False

# =====================================================
# AZURE KEY VAULT
# =====================================================
AZURE_KEY_VAULT_NAME=$KeyVaultName
AZURE_KEY_VAULT_URI=https://$KeyVaultName.vault.azure.net/

# =====================================================
# DJANGO SETTINGS
# =====================================================
DEBUG=True
SECRET_KEY=django-insecure-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1
"@

Set-Content -Path ".env.azure" -Value $envContent
Write-Host "✅ Archivo .env.azure creado" -ForegroundColor Green

# =====================================================
# SUMMARY
# =====================================================
Write-Host "`n========================================"  -ForegroundColor Cyan
Write-Host "📊 RESUMEN DEL DEPLOYMENT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`n✅ ¡Deployment completado exitosamente!" -ForegroundColor Green
Write-Host "`n📦 RECURSOS CREADOS:" -ForegroundColor Cyan
Write-Host "`n1. PostgreSQL Database:" -ForegroundColor Blue
Write-Host "   Server: $PostgresHost"
Write-Host "   Database: $PostgresDb"
Write-Host "   Usuario: $PostgresAdmin"
Write-Host "   Password: $PostgresPassword"

Write-Host "`n2. Redis Cache:" -ForegroundColor Blue
Write-Host "   Host: $RedisHost"
Write-Host "   Port: 6380 (SSL)"

Write-Host "`n3. Cosmos DB (MongoDB):" -ForegroundColor Blue
Write-Host "   Account: $CosmosAccount"
Write-Host "   Database: upeu_documents"

Write-Host "`n4. Key Vault:" -ForegroundColor Blue
Write-Host "   Name: $KeyVaultName"
Write-Host "   URI: https://$KeyVaultName.vault.azure.net/"

Write-Host "`n💰 COSTOS ESTIMADOS:" -ForegroundColor Cyan
Write-Host "   PostgreSQL: ~`$15/mes"
Write-Host "   Redis: ~`$16/mes"
Write-Host "   Cosmos DB: ~`$5-10/mes"
Write-Host "   ─────────────────────"
Write-Host "   TOTAL: ~`$36-41/mes" -ForegroundColor Green

Write-Host "`n🚀 PRÓXIMOS PASOS:" -ForegroundColor Cyan
Write-Host "1. Copiar configuración:"
Write-Host "   cp .env.azure .env" -ForegroundColor Yellow
Write-Host "`n2. Probar conexión:"
Write-Host "   python manage.py check" -ForegroundColor Yellow
Write-Host "   python manage.py migrate" -ForegroundColor Yellow
Write-Host "`n3. Crear superusuario:"
Write-Host "   python manage.py createsuperuser" -ForegroundColor Yellow

Write-Host "`n✨ ¡Todo listo! Tus bases de datos están en la nube." -ForegroundColor Green
Write-Host ""
