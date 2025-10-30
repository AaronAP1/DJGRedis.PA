# =====================================================
# DEPLOYMENT RÁPIDO DE DJANGO A AZURE APP SERVICE
# Sistema PPP UPeU
# =====================================================

param(
    [string]$ResourceGroup = "rg-upeu-ppp-students",
    [string]$Location = "brazilsouth",
    [string]$AppServicePlan = "asp-upeu-ppp",
    [string]$WebApp = "upeu-ppp-api-$(Get-Random -Minimum 1000 -Maximum 9999)"
)

$ErrorActionPreference = "Continue"

Clear-Host
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DJANGO APP SERVICE DEPLOYMENT" -ForegroundColor Cyan
Write-Host "  API REST para Sistema PPP UPeU" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# VERIFICAR LOGIN
Write-Host "`n[1/8] Verificando autenticacion Azure..." -ForegroundColor Cyan
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "[ERROR] No autenticado" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Conectado como: $($account.user.name)" -ForegroundColor Green

# REGISTRAR RESOURCE PROVIDER
Write-Host "`n[2/8] Registrando Microsoft.Web provider..." -ForegroundColor Cyan
$webProvider = az provider show --namespace Microsoft.Web --query "registrationState" -o tsv 2>$null
if ($webProvider -ne "Registered") {
    Write-Host "   Registrando provider (puede tomar 1-2 min)..." -ForegroundColor Yellow
    az provider register --namespace Microsoft.Web --wait --output none
    Write-Host "[OK] Provider registrado" -ForegroundColor Green
} else {
    Write-Host "[SKIP] Ya registrado" -ForegroundColor Yellow
}

# CONFIGURACIÓN
Write-Host "`n[3/8] Configuracion:" -ForegroundColor Cyan
Write-Host "  Resource Group: $ResourceGroup" -ForegroundColor White
Write-Host "  App Service:    $WebApp" -ForegroundColor White
Write-Host "  Location:       $Location" -ForegroundColor White
Write-Host "  SKU:            F1 (Free)" -ForegroundColor Green
Write-Host ""
Write-Host "  URL final:      https://$WebApp.azurewebsites.net" -ForegroundColor Yellow
Write-Host ""

$confirm = Read-Host "Continuar? (Y/N)"
if ($confirm -ne 'Y' -and $confirm -ne 'y') { 
    Write-Host "Cancelado" -ForegroundColor Yellow
    exit 0 
}

# CREATE APP SERVICE PLAN
Write-Host "`n[4/8] Creando App Service Plan..." -ForegroundColor Cyan
$planExists = az appservice plan show --name $AppServicePlan -g $ResourceGroup 2>$null

if ($planExists) {
    Write-Host "[SKIP] Ya existe: $AppServicePlan" -ForegroundColor Yellow
} else {
    az appservice plan create `
        --name $AppServicePlan `
        --resource-group $ResourceGroup `
        --location $Location `
        --is-linux `
        --sku F1 `
        --output none
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] App Service Plan creado" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Fallo al crear App Service Plan" -ForegroundColor Red
        exit 1
    }
}

# CREATE WEB APP
Write-Host "`n[5/8] Creando Web App..." -ForegroundColor Cyan
az webapp create `
    --name $WebApp `
    --resource-group $ResourceGroup `
    --plan $AppServicePlan `
    --runtime "PYTHON:3.11" `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Web App creada: $WebApp" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Fallo al crear Web App" -ForegroundColor Red
    exit 1
}

# CONFIGURAR VARIABLES DE ENTORNO
Write-Host "`n[6/8] Configurando variables de entorno..." -ForegroundColor Cyan

# Leer .env.azure
$envVars = @{}
Get-Content ".env.azure" | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        $envVars[$key] = $value
    }
}

# Agregar variables críticas
$envVars["SCM_DO_BUILD_DURING_DEPLOYMENT"] = "true"
$envVars["ENABLE_ORYX_BUILD"] = "true"
$envVars["POST_BUILD_COMMAND"] = "python manage.py migrate"
$envVars["WEBSITE_HTTPLOGGING_RETENTION_DAYS"] = "7"

Write-Host "   Configurando $($envVars.Count) variables..." -ForegroundColor Cyan

foreach ($key in $envVars.Keys) {
    az webapp config appsettings set `
        --name $WebApp `
        --resource-group $ResourceGroup `
        --settings "$key=$($envVars[$key])" `
        --output none
}

Write-Host "[OK] Variables configuradas" -ForegroundColor Green

# CONFIGURAR STARTUP COMMAND
Write-Host "`n[7/8] Configurando startup command..." -ForegroundColor Cyan

az webapp config set `
    --name $WebApp `
    --resource-group $ResourceGroup `
    --startup-file "gunicorn --bind=0.0.0.0 --timeout 600 config.wsgi" `
    --output none

Write-Host "[OK] Startup configurado" -ForegroundColor Green

# DEPLOY CODE
Write-Host "`n[8/8] Desplegando codigo..." -ForegroundColor Cyan
Write-Host "[INFO] Esto tomara 5-10 minutos..." -ForegroundColor Yellow

# Crear archivo .deployment si no existe
@"
[config]
SCM_DO_BUILD_DURING_DEPLOYMENT=true
"@ | Out-File -FilePath ".deployment" -Encoding UTF8

az webapp up `
    --name $WebApp `
    --resource-group $ResourceGroup `
    --runtime "PYTHON:3.11" `
    --sku F1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Codigo desplegado" -ForegroundColor Green
} else {
    Write-Host "[WARN] Deployment con warnings, verificar logs" -ForegroundColor Yellow
}

# SUMMARY
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT COMPLETADO" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "URLs IMPORTANTES:" -ForegroundColor Yellow
Write-Host "  API:       https://$WebApp.azurewebsites.net" -ForegroundColor White
Write-Host "  Admin:     https://$WebApp.azurewebsites.net/admin" -ForegroundColor White
Write-Host "  Swagger:   https://$WebApp.azurewebsites.net/swagger" -ForegroundColor White
Write-Host "  GraphQL:   https://$WebApp.azurewebsites.net/graphql" -ForegroundColor White
Write-Host ""
Write-Host "LOGS:" -ForegroundColor Yellow
Write-Host "  az webapp log tail --name $WebApp -g $ResourceGroup" -ForegroundColor White
Write-Host ""
Write-Host "COSTO: `$0/mes (Free Tier F1)" -ForegroundColor Green
Write-Host ""
