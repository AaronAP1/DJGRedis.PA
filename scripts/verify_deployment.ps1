# =====================================================
# VERIFICACIÓN POST-DEPLOYMENT
# Sistema PPP UPeU - Azure App Service
# =====================================================

param(
    [string]$WebAppName = "upeu-ppp-api-5983",
    [string]$ResourceGroup = "rg-upeu-ppp-students"
)

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  POST-DEPLOYMENT VERIFICATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$baseUrl = "https://$WebAppName.azurewebsites.net"

# 1. VERIFICAR ESTADO DE LA APP
Write-Host "`n[1/6] Verificando estado de la webapp..." -ForegroundColor Cyan
$appState = az webapp show --name $WebAppName -g $ResourceGroup --query "state" -o tsv
Write-Host "   Estado: $appState" -ForegroundColor $(if ($appState -eq "Running") { "Green" } else { "Red" })

# 2. VERIFICAR DEPLOYMENT STATUS
Write-Host "`n[2/6] Verificando ultimo deployment..." -ForegroundColor Cyan
$lastDeployment = az webapp deployment list --name $WebAppName -g $ResourceGroup --query "[0]" | ConvertFrom-Json
if ($lastDeployment) {
    Write-Host "   ID: $($lastDeployment.id.Split('/')[-1])" -ForegroundColor White
    Write-Host "   Status: $($lastDeployment.status)" -ForegroundColor $(if ($lastDeployment.status -eq 4) { "Green" } else { "Yellow" })
    Write-Host "   Time: $($lastDeployment.start_time)" -ForegroundColor White
}

# 3. TEST ENDPOINT RAÍZ
Write-Host "`n[3/6] Testeando endpoint raiz..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri $baseUrl -Method GET -TimeoutSec 10 -UseBasicParsing
    Write-Host "   Status Code: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   La app podria estar iniciando..." -ForegroundColor Yellow
}

# 4. TEST ADMIN ENDPOINT
Write-Host "`n[4/6] Testeando /admin..." -ForegroundColor Cyan
try {
    $adminUrl = "$baseUrl/admin/"
    $response = Invoke-WebRequest -Uri $adminUrl -Method GET -TimeoutSec 10 -UseBasicParsing
    Write-Host "   Status Code: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Yellow
}

# 5. TEST API ENDPOINT
Write-Host "`n[5/6] Testeando /api/..." -ForegroundColor Cyan
try {
    $apiUrl = "$baseUrl/api/"
    $response = Invoke-WebRequest -Uri $apiUrl -Method GET -TimeoutSec 10 -UseBasicParsing
    Write-Host "   Status Code: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Yellow
}

# 6. MOSTRAR ÚLTIMOS LOGS
Write-Host "`n[6/6] Mostrando ultimos logs..." -ForegroundColor Cyan
Write-Host "   Ejecutando: az webapp log tail --name $WebAppName -g $ResourceGroup" -ForegroundColor White
Write-Host ""

# SUMMARY
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  URLs IMPORTANTES" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Base URL:   $baseUrl" -ForegroundColor White
Write-Host "  Admin:      $baseUrl/admin/" -ForegroundColor White
Write-Host "  Swagger:    $baseUrl/swagger/" -ForegroundColor White
Write-Host "  GraphQL:    $baseUrl/graphql/" -ForegroundColor White
Write-Host ""
Write-Host "COMANDOS UTILES:" -ForegroundColor Yellow
Write-Host "  Ver logs:     az webapp log tail --name $WebAppName -g $ResourceGroup" -ForegroundColor White
Write-Host "  Restart:      az webapp restart --name $WebAppName -g $ResourceGroup" -ForegroundColor White
Write-Host "  SSH:          az webapp ssh --name $WebAppName -g $ResourceGroup" -ForegroundColor White
Write-Host "  Bajar a F1:   az appservice plan update --name asp-upeu-ppp -g $ResourceGroup --sku F1" -ForegroundColor White
Write-Host ""

# OPCIONAL: Ver logs en tiempo real
$viewLogs = Read-Host "Ver logs en tiempo real? (Y/N)"
if ($viewLogs -eq 'Y' -or $viewLogs -eq 'y') {
    az webapp log tail --name $WebAppName -g $ResourceGroup
}
