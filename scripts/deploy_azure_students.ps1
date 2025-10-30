# =====================================================
# AZURE FOR STUDENTS - DATABASE DEPLOYMENT
# Sistema PPP UPeU - Optimizado para Students
# =====================================================

param(
    [ValidateSet('brazilsouth','chilecentral','northcentralus','mexicocentral','canadacentral')]
    [string]$Location = "brazilsouth",
    [string]$ResourceGroup = "rg-upeu-ppp-students",
    [string]$PostgresServer = "psql-upeu-ppp-$(Get-Random -Minimum 1000 -Maximum 9999)",
    [string]$RedisName = "redis-upeu-ppp-$(Get-Random -Minimum 1000 -Maximum 9999)",
    [string]$CosmosAccount = "cosmos-upeu-ppp-$(Get-Random -Minimum 1000 -Maximum 9999)"
)

$ErrorActionPreference = "Continue"

Clear-Host
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AZURE FOR STUDENTS - DB DEPLOYMENT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# VERIFY PROVIDERS
Write-Host "[1/9] Verificando Resource Providers..." -ForegroundColor Cyan
$providers = @('Microsoft.DBforPostgreSQL', 'Microsoft.Cache', 'Microsoft.DocumentDB')
$allRegistered = $true

foreach ($provider in $providers) {
    $status = az provider show -n $provider --query registrationState -o tsv 2>$null
    if ($status -eq 'Registered') {
        Write-Host "  [OK] $provider" -ForegroundColor Green
    } else {
        Write-Host "  [WAIT] $provider ($status)" -ForegroundColor Yellow
        $allRegistered = $false
    }
}

if (-not $allRegistered) {
    Write-Host ""
    Write-Host "[ACTION] Registrando providers pendientes..." -ForegroundColor Yellow
    az provider register --namespace Microsoft.DBforPostgreSQL --wait
    az provider register --namespace Microsoft.Cache --wait
    az provider register --namespace Microsoft.DocumentDB --wait
    Write-Host "[OK] Todos los providers registrados" -ForegroundColor Green
}

# CHECK LOGIN
Write-Host "`n[2/9] Verificando autenticacion..." -ForegroundColor Cyan
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "[ERROR] No autenticado. Ejecuta: az login" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Usuario: $($account.user.name)" -ForegroundColor Green
Write-Host "     Suscripcion: $($account.name)" -ForegroundColor White

if ($account.name -notlike "*Students*") {
    Write-Host "[WARN] No es Azure for Students!" -ForegroundColor Yellow
    $continue = Read-Host "Continuar de todos modos? (Y/N)"
    if ($continue -ne 'Y' -and $continue -ne 'y') { exit 0 }
}

# SHOW CONFIG
Write-Host "`n[3/9] Configuracion:" -ForegroundColor Cyan
Write-Host "  Region:         $Location" -ForegroundColor White
Write-Host "  Resource Group: $ResourceGroup" -ForegroundColor White
Write-Host "  PostgreSQL:     $PostgresServer" -ForegroundColor White
Write-Host "  Redis:          $RedisName" -ForegroundColor White
Write-Host "  Cosmos DB:      $CosmosAccount" -ForegroundColor White
Write-Host ""
Write-Host "  Costos: ~`$36-41/mes (GRATIS con Students)" -ForegroundColor Green
Write-Host ""

$confirm = Read-Host "Iniciar deployment? (Y/N)"
if ($confirm -ne 'Y' -and $confirm -ne 'y') { 
    Write-Host "Cancelado" -ForegroundColor Yellow
    exit 0 
}

# CREATE RESOURCE GROUP
Write-Host "`n[4/9] Creando Resource Group..." -ForegroundColor Cyan
$exists = az group exists --name $ResourceGroup
if ($exists -eq 'true') {
    Write-Host "[OK] Ya existe: $ResourceGroup" -ForegroundColor Yellow
} else {
    az group create --name $ResourceGroup --location $Location --output table
    Write-Host "[OK] Creado: $ResourceGroup" -ForegroundColor Green
}

# GENERATE STRONG PASSWORD
$postgresPass = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 24 | ForEach-Object {[char]$_})
$postgresAdmin = "upeuadmin"
$postgresDb = "upeu_ppp_system"

# CREATE POSTGRESQL
Write-Host "`n[5/9] Creando PostgreSQL Flexible Server..." -ForegroundColor Cyan
Write-Host "[INFO] Esto tomara 8-12 minutos..." -ForegroundColor Yellow

$pgCmd = "az postgres flexible-server create " +
         "--name $PostgresServer " +
         "--resource-group $ResourceGroup " +
         "--location $Location " +
         "--admin-user $postgresAdmin " +
         "--admin-password `"$postgresPass`" " +
         "--sku-name Standard_B1ms " +
         "--tier Burstable " +
         "--storage-size 32 " +
         "--version 15 " +
         "--public-access 0.0.0.0-255.255.255.255 " +
         "--backup-retention 7"

Invoke-Expression $pgCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] PostgreSQL creado exitosamente" -ForegroundColor Green
    
    # CREATE DATABASE
    Write-Host "     Creando database $postgresDb..." -ForegroundColor Cyan
    az postgres flexible-server db create `
        --resource-group $ResourceGroup `
        --server-name $PostgresServer `
        --database-name $postgresDb
    
    # ADD FIREWALL RULE
    Write-Host "     Agregando regla de firewall..." -ForegroundColor Cyan
    $myIp = (Invoke-WebRequest -Uri "https://api.ipify.org" -UseBasicParsing).Content.Trim()
    az postgres flexible-server firewall-rule create `
        --resource-group $ResourceGroup `
        --name $PostgresServer `
        --rule-name AllowMyIP `
        --start-ip-address $myIp `
        --end-ip-address $myIp
} else {
    Write-Host "[ERROR] Fallo al crear PostgreSQL" -ForegroundColor Red
    exit 1
}

# CREATE REDIS
Write-Host "`n[6/9] Creando Redis Cache..." -ForegroundColor Cyan
Write-Host "[INFO] Esto tomara 12-18 minutos..." -ForegroundColor Yellow

az redis create `
    --name $RedisName `
    --resource-group $ResourceGroup `
    --location $Location `
    --sku Basic `
    --vm-size c0 `
    --minimum-tls-version 1.2

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Redis creado exitosamente" -ForegroundColor Green
    
    $redisKey = az redis list-keys --name $RedisName --resource-group $ResourceGroup --query primaryKey -o tsv
    $redisHost = "$RedisName.redis.cache.windows.net"
} else {
    Write-Host "[ERROR] Fallo al crear Redis" -ForegroundColor Red
    exit 1
}

# CREATE COSMOS DB
Write-Host "`n[7/9] Creando Cosmos DB (MongoDB)..." -ForegroundColor Cyan
Write-Host "[INFO] Esto tomara 8-12 minutos..." -ForegroundColor Yellow

az cosmosdb create `
    --name $CosmosAccount `
    --resource-group $ResourceGroup `
    --kind MongoDB `
    --server-version 6.0 `
    --default-consistency-level Session `
    --locations regionName=$Location failoverPriority=0 `
    --capabilities EnableServerless

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Cosmos DB creado exitosamente" -ForegroundColor Green
    
    # CREATE DATABASE
    Write-Host "     Creando MongoDB database..." -ForegroundColor Cyan
    az cosmosdb mongodb database create `
        --account-name $CosmosAccount `
        --resource-group $ResourceGroup `
        --name upeu_documents
    
    $cosmosConn = az cosmosdb keys list `
        --name $CosmosAccount `
        --resource-group $ResourceGroup `
        --type connection-strings `
        --query "connectionStrings[0].connectionString" -o tsv
} else {
    Write-Host "[ERROR] Fallo al crear Cosmos DB" -ForegroundColor Red
    exit 1
}

# GENERATE .ENV FILE
Write-Host "`n[8/9] Generando configuracion..." -ForegroundColor Cyan

$postgresHost = "$PostgresServer.postgres.database.azure.com"
$postgresUrl = "postgres://${postgresAdmin}:${postgresPass}@${postgresHost}:5432/${postgresDb}?sslmode=require"
$redisUrl = "rediss://:${redisKey}@${redisHost}:6380/0"

$envContent = @"
# =====================================================
# AZURE FOR STUDENTS - AUTO-GENERATED
# Fecha: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# Region: $Location
# =====================================================

# POSTGRESQL
DB_NAME=$postgresDb
DB_USER=$postgresAdmin
DB_PASSWORD=$postgresPass
DB_HOST=$postgresHost
DB_PORT=5432
DATABASE_URL=$postgresUrl

# REDIS CACHE
REDIS_HOST=$redisHost
REDIS_PORT=6380
REDIS_PASSWORD=$redisKey
USE_REDIS_CACHE=True
REDIS_URL=$redisUrl

# MONGODB (COSMOS DB)
MONGODB_DB_NAME=upeu_documents
MONGODB_URI=$cosmosConn

# CELERY
CELERY_BROKER_URL=$redisUrl
CELERY_RESULT_BACKEND=$redisUrl
CELERY_TASK_ALWAYS_EAGER=False

# AZURE
AZURE_RESOURCE_GROUP=$ResourceGroup
AZURE_LOCATION=$Location

# DJANGO SETTINGS
DEBUG=True
SECRET_KEY=django-insecure-$(Get-Random)-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOW_ALL_ORIGINS=True
"@

$envContent | Out-File -FilePath ".env.azure" -Encoding UTF8
Write-Host "[OK] Archivo .env.azure creado" -ForegroundColor Green

# SAVE CREDENTIALS
Write-Host "`n[9/9] Guardando credenciales..." -ForegroundColor Cyan
$credFile = "azure_credentials_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
$credContent = @"
========================================
AZURE FOR STUDENTS - CREDENCIALES
========================================

POSTGRESQL:
  Host: $postgresHost
  Port: 5432
  Database: $postgresDb
  Usuario: $postgresAdmin
  Password: $postgresPass
  
  Connection String:
  $postgresUrl

REDIS CACHE:
  Host: $redisHost
  Port: 6380 (SSL)
  Password: $redisKey
  
  Connection String:
  $redisUrl

COSMOS DB (MONGODB):
  Account: $CosmosAccount
  Database: upeu_documents
  
  Connection String:
  $cosmosConn

RESOURCE GROUP:
  Nombre: $ResourceGroup
  Region: $Location
  
COSTOS:
  PostgreSQL B1ms: ~`$15/mes
  Redis C0: ~`$16/mes
  Cosmos Serverless: ~`$5-10/mes
  TOTAL: ~`$36-41/mes
  
  Con Azure Students: `$0/mes (incluido en credito)

========================================
GENERADO: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
========================================
"@

$credContent | Out-File -FilePath $credFile -Encoding UTF8
Write-Host "[OK] Credenciales guardadas en: $credFile" -ForegroundColor Green

# SUMMARY
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT COMPLETADO EXITOSAMENTE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "RECURSOS CREADOS:" -ForegroundColor Yellow
Write-Host "  PostgreSQL: $postgresHost" -ForegroundColor White
Write-Host "  Redis:      $redisHost" -ForegroundColor White
Write-Host "  Cosmos DB:  $CosmosAccount.mongo.cosmos.azure.com" -ForegroundColor White
Write-Host ""
Write-Host "ARCHIVOS GENERADOS:" -ForegroundColor Yellow
Write-Host "  .env.azure           -> Variables de entorno" -ForegroundColor White
Write-Host "  $credFile -> Credenciales backup" -ForegroundColor White
Write-Host ""
Write-Host "PROXIMOS PASOS:" -ForegroundColor Cyan
Write-Host "  1. cp .env.azure .env" -ForegroundColor White
Write-Host "  2. python manage.py check" -ForegroundColor White
Write-Host "  3. python manage.py migrate" -ForegroundColor White
Write-Host "  4. python manage.py createsuperuser" -ForegroundColor White
Write-Host ""
Write-Host "COSTO MENSUAL: `$0 (incluido en Azure Students)" -ForegroundColor Green
Write-Host ""
