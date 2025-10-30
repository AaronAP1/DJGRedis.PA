# =====================================================
# AZURE DATABASES DEPLOYMENT - PowerShell
# Sistema PPP UPeU - Solo Bases de Datos
# =====================================================

param(
    [string]$ResourceGroup = "rg-upeu-ppp-databases",
    [string]$Location = "brazilsouth",  # CAMBIADO: Azure Students solo permite estas regiones
    [string]$PostgresServer = "psql-upeu-ppp",
    [string]$PostgresDb = "upeu_ppp_system",
    [string]$PostgresAdmin = "upeu_admin",
    [string]$RedisName = "redis-upeu-ppp",
    [string]$CosmosAccount = "cosmos-upeu-ppp",
    [string]$KeyVaultName = "kv-upeu-ppp-db"
)

$ErrorActionPreference = "Stop"

Clear-Host
Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  AZURE DATABASES DEPLOYMENT - UPeU PPP" -ForegroundColor Cyan
Write-Host "  PostgreSQL + Redis + Cosmos DB" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# CHECK AZURE CLI
Write-Host "`n[1/8] Verificando Azure CLI..." -ForegroundColor Cyan
try {
    $null = az version
    Write-Host "[OK] Azure CLI instalado" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Azure CLI no encontrado" -ForegroundColor Red
    Write-Host "Instalar: https://aka.ms/installazurecliwindows"
    exit 1
}

# CHECK LOGIN
Write-Host "`n[2/8] Verificando autenticacion..." -ForegroundColor Cyan
try {
    $account = az account show | ConvertFrom-Json
    Write-Host "[OK] Conectado como: $($account.user.name)" -ForegroundColor Green
    Write-Host "     Suscripcion: $($account.name)" -ForegroundColor White
    
    if ($account.name -like "*Students*") {
        Write-Host "     [STUDENTS] Credito `$100/mes disponible!" -ForegroundColor Green
    }
} catch {
    Write-Host "[WARN] No autenticado. Iniciando login..." -ForegroundColor Yellow
    az login
}

# SHOW COSTS AND REGION
Write-Host "`n[3/8] Configuracion:" -ForegroundColor Cyan
Write-Host "  Region: $Location (permitida para Students)" -ForegroundColor White
Write-Host ""
Write-Host "  Costos estimados:" -ForegroundColor Cyan
Write-Host "    PostgreSQL (B1ms): ~`$15/mes" -ForegroundColor White
Write-Host "    Redis (C0):        ~`$16/mes" -ForegroundColor White
Write-Host "    Cosmos DB:         ~`$5-10/mes" -ForegroundColor White
Write-Host "    Key Vault:         ~`$0.03/mes" -ForegroundColor White
Write-Host "    --------------------------------" -ForegroundColor DarkGray
Write-Host "    TOTAL:             ~`$36-41/mes" -ForegroundColor Yellow
Write-Host "    Con Students:      `$0/mes (GRATIS)" -ForegroundColor Green

$confirm = Read-Host "`nContinuar con $Location? (Y/N)"
if ($confirm -ne 'Y' -and $confirm -ne 'y') { Write-Host "Cancelado" -ForegroundColor Yellow; exit 0 }

# CREATE RESOURCE GROUP
Write-Host "`n[4/8] Creando Resource Group..." -ForegroundColor Cyan
$exists = az group exists --name $ResourceGroup
if ($exists -eq 'true') {
    Write-Host "[SKIP] Ya existe: $ResourceGroup" -ForegroundColor Yellow
} else {
    az group create --name $ResourceGroup --location $Location --output none
    Write-Host "[OK] Creado: $ResourceGroup" -ForegroundColor Green
}

# CREATE KEY VAULT
Write-Host "`n[5/8] Creando Key Vault..." -ForegroundColor Cyan
try {
    $null = az keyvault show --name $KeyVaultName -g $ResourceGroup 2>$null
    Write-Host "[SKIP] Ya existe: $KeyVaultName" -ForegroundColor Yellow
} catch {
    az keyvault create --name $KeyVaultName -g $ResourceGroup -l $Location --output none
    Write-Host "[OK] Creado: $KeyVaultName" -ForegroundColor Green
}

# CREATE POSTGRESQL
Write-Host "`n[6/8] Creando PostgreSQL..." -ForegroundColor Cyan
$postgresPass = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 20 | ForEach-Object {[char]$_})

try {
    $checkServer = az postgres flexible-server show --name $PostgresServer -g $ResourceGroup 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SKIP] Ya existe: $PostgresServer" -ForegroundColor Yellow
        try {
            $postgresPass = az keyvault secret show --vault-name $KeyVaultName --name "postgres-password" --query value -o tsv 2>$null
        } catch {
            Write-Host "[WARN] No se pudo recuperar password del Key Vault" -ForegroundColor Yellow
        }
    } else {
        throw "Not found"
    }
} catch {
    Write-Host "[WAIT] Creando PostgreSQL (8-12 min)..." -ForegroundColor Yellow
    
    $pgResult = az postgres flexible-server create `
        --name $PostgresServer -g $ResourceGroup -l $Location `
        --admin-user $PostgresAdmin --admin-password $postgresPass `
        --sku-name Standard_B1ms --tier Burstable `
        --storage-size 32 --version 15 `
        --public-access 0.0.0.0-255.255.255.255 `
        --backup-retention 7 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Fallo al crear PostgreSQL:" -ForegroundColor Red
        Write-Host $pgResult -ForegroundColor Red
        exit 1
    }
    
    Write-Host "[OK] PostgreSQL creado" -ForegroundColor Green
    
    # Guardar password en Key Vault
    $null = az keyvault secret set --vault-name $KeyVaultName --name "postgres-password" --value "$postgresPass" 2>$null
    
    Write-Host "      Creando database..." -ForegroundColor Cyan
    az postgres flexible-server db create `
        -g $ResourceGroup --server-name $PostgresServer `
        --database-name $PostgresDb --output none
    
    Write-Host "      Configurando firewall..." -ForegroundColor Cyan
    $myIp = (Invoke-WebRequest -Uri "https://api.ipify.org" -UseBasicParsing).Content.Trim()
    az postgres flexible-server firewall-rule create `
        -g $ResourceGroup --name $PostgresServer `
        --rule-name "AllowMyIP" `
        --start-ip-address $myIp --end-ip-address $myIp --output none
}

# CREATE REDIS
Write-Host "`n[7/8] Creando Redis Cache..." -ForegroundColor Cyan
try {
    $checkRedis = az redis show --name $RedisName -g $ResourceGroup 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SKIP] Ya existe: $RedisName" -ForegroundColor Yellow
    } else {
        throw "Not found"
    }
} catch {
    Write-Host "[WAIT] Creando Redis (12-18 min)..." -ForegroundColor Yellow
    
    # CORREGIDO: Sintaxis correcta para PowerShell
    $redisResult = az redis create `
        --name $RedisName -g $ResourceGroup -l $Location `
        --sku Basic --vm-size c0 `
        --minimum-tls-version 1.2 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Fallo al crear Redis:" -ForegroundColor Red
        Write-Host $redisResult -ForegroundColor Red
        exit 1
    }
    
    Write-Host "[OK] Redis creado" -ForegroundColor Green
}

$redisKey = az redis list-keys --name $RedisName -g $ResourceGroup --query primaryKey -o tsv 2>$null
if ($redisKey) {
    $null = az keyvault secret set --vault-name $KeyVaultName --name "redis-key" --value "$redisKey" 2>$null
}

# CREATE COSMOS DB
Write-Host "`n[8/8] Creando Cosmos DB..." -ForegroundColor Cyan
try {
    $checkCosmos = az cosmosdb show --name $CosmosAccount -g $ResourceGroup 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SKIP] Ya existe: $CosmosAccount" -ForegroundColor Yellow
    } else {
        throw "Not found"
    }
} catch {
    Write-Host "[WAIT] Creando Cosmos DB (8-12 min)..." -ForegroundColor Yellow
    
    $cosmosResult = az cosmosdb create `
        --name $CosmosAccount -g $ResourceGroup `
        --kind MongoDB --server-version 6.0 `
        --default-consistency-level Session `
        --locations regionName=$Location failoverPriority=0 `
        --capabilities EnableServerless 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Fallo al crear Cosmos DB:" -ForegroundColor Red
        Write-Host $cosmosResult -ForegroundColor Red
        exit 1
    }
    
    Write-Host "[OK] Cosmos DB creado" -ForegroundColor Green
    
    Write-Host "      Creando database MongoDB..." -ForegroundColor Cyan
    az cosmosdb mongodb database create `
        --account-name $CosmosAccount -g $ResourceGroup `
        --name upeu_documents --output none
}

$cosmosConn = az cosmosdb keys list `
    --name $CosmosAccount -g $ResourceGroup `
    --type connection-strings `
    --query "connectionStrings[0].connectionString" -o tsv 2>$null

if ($cosmosConn) {
    $null = az keyvault secret set --vault-name $KeyVaultName --name "cosmos-connection-string" --value "$cosmosConn" 2>$null
}

# GENERATE .ENV FILE
Write-Host "`nGenerando archivo .env.azure..." -ForegroundColor Cyan

$postgresHost = "$PostgresServer.postgres.database.azure.com"
$postgresUrl = "postgres://${PostgresAdmin}:${postgresPass}@${postgresHost}:5432/${PostgresDb}?sslmode=require"
$redisHost = "$RedisName.redis.cache.windows.net"
$redisUrl = "rediss://:${redisKey}@${redisHost}:6380/0"

$envFile = @"
# Azure Databases - Auto-generated $(Get-Date -Format "yyyy-MM-dd HH:mm")
# Resource Group: $ResourceGroup

# POSTGRESQL
DB_NAME=$PostgresDb
DB_USER=$PostgresAdmin
DB_PASSWORD=$postgresPass
DB_HOST=$postgresHost
DB_PORT=5432
DATABASE_URL=$postgresUrl

# REDIS
REDIS_HOST=$redisHost
REDIS_PORT=6380
REDIS_PASSWORD=$redisKey
USE_REDIS_CACHE=True
REDIS_URL=$redisUrl

# MONGODB (Cosmos DB)
MONGODB_DB_NAME=upeu_documents
MONGODB_URI=$cosmosConn

# CELERY
CELERY_BROKER_URL=$redisUrl
CELERY_RESULT_BACKEND=$redisUrl
CELERY_TASK_ALWAYS_EAGER=False

# AZURE
AZURE_KEY_VAULT_NAME=$KeyVaultName
AZURE_KEY_VAULT_URI=https://$KeyVaultName.vault.azure.net/

# DJANGO (ajustar segun necesidad)
DEBUG=True
SECRET_KEY=django-insecure-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1
"@

$envFile | Out-File -FilePath ".env.azure" -Encoding UTF8 -NoNewline
Write-Host "[OK] Archivo .env.azure creado" -ForegroundColor Green

# SUMMARY
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT COMPLETADO" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nRECURSOS CREADOS:" -ForegroundColor Yellow
Write-Host "  PostgreSQL: $postgresHost"
Write-Host "    Database: $PostgresDb"
Write-Host "    Usuario:  $PostgresAdmin"
Write-Host "    Password: $postgresPass"
Write-Host "`n  Redis:      $redisHost"
Write-Host "    Port:     6380 (SSL)"
Write-Host "`n  Cosmos DB:  $CosmosAccount.mongo.cosmos.azure.com"
Write-Host "    Database: upeu_documents"
Write-Host "`n  Key Vault:  https://$KeyVaultName.vault.azure.net/"

Write-Host "`nCOSTOS: ~`$36-41/mes (GRATIS con Azure Students)" -ForegroundColor Yellow

Write-Host "`nPROXIMOS PASOS:" -ForegroundColor Cyan
Write-Host "  1. cp .env.azure .env" -ForegroundColor White
Write-Host "  2. python manage.py check" -ForegroundColor White
Write-Host "  3. python manage.py migrate" -ForegroundColor White
Write-Host "  4. python manage.py createsuperuser" -ForegroundColor White

Write-Host "`n[SUCCESS] Tus bases de datos estan listas en Azure!" -ForegroundColor Green
Write-Host ""
