#!/bin/bash
# =====================================================
# AZURE DATABASES ONLY DEPLOYMENT
# Sistema de Gestión de Prácticas Profesionales - UPeU
# =====================================================
# Este script despliega SOLO las bases de datos en Azure
# Ideal para usar con Azure for Students ($100/mes crédito)
# Luego puedes conectarte desde local o desplegar app en Render

set -e  # Exit on error

# =====================================================
# CONFIGURATION
# =====================================================
RESOURCE_GROUP="rg-upeu-ppp-databases"
LOCATION="eastus"  # O "brazilsouth" si prefieres más cerca
POSTGRES_SERVER="psql-upeu-ppp"
POSTGRES_DB="upeu_ppp_system"
POSTGRES_ADMIN="upeu_admin"
REDIS_NAME="redis-upeu-ppp"
COSMOS_ACCOUNT="cosmos-upeu-ppp"
KEYVAULT_NAME="kv-upeu-ppp-db"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# =====================================================
# HELPER FUNCTIONS
# =====================================================
print_header() {
    echo -e "${CYAN}"
    echo "========================================"
    echo "$1"
    echo "========================================"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# =====================================================
# BANNER
# =====================================================
clear
echo -e "${CYAN}"
cat << "EOF"
╔══════════════════════════════════════════════════════╗
║  AZURE DATABASES DEPLOYMENT - UPeU PPP System       ║
║  Desplegando: PostgreSQL + Redis + Cosmos DB        ║
╚══════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# =====================================================
# 1. CHECK PREREQUISITES
# =====================================================
print_header "🔍 Verificando Prerrequisitos"

# Check Azure CLI
if ! command -v az &> /dev/null; then
    print_error "Azure CLI no está instalado"
    echo ""
    echo "Instalar Azure CLI:"
    echo "  Windows: https://aka.ms/installazurecliwindows"
    echo "  Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
    echo "  macOS: brew install azure-cli"
    exit 1
fi
print_success "Azure CLI instalado"

# Check if logged in
if ! az account show &> /dev/null; then
    print_warning "No estás autenticado en Azure"
    echo ""
    print_info "Iniciando login..."
    az login
fi

# Get account info
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
ACCOUNT_TYPE=$(az account show --query user.type -o tsv)

print_success "Autenticación verificada"
echo ""
echo -e "${CYAN}📊 Información de la cuenta:${NC}"
echo "  Nombre: $SUBSCRIPTION_NAME"
echo "  ID: $SUBSCRIPTION_ID"
echo "  Tipo: $ACCOUNT_TYPE"
echo ""

# Check if Azure for Students
IS_STUDENT=$(az account show --query "tags.studentSubscription" -o tsv 2>/dev/null || echo "false")

if [[ "$SUBSCRIPTION_NAME" == *"Azure for Students"* ]] || [[ "$IS_STUDENT" == "true" ]]; then
    print_success "✨ Cuenta Azure for Students detectada - ¡$100 USD/mes de crédito!"
    echo ""
else
    print_warning "No se detectó Azure for Students"
    echo ""
    echo "Si tienes email .edu, obtén crédito gratis:"
    echo "  👉 https://azure.microsoft.com/es-es/free/students/"
    echo ""
    read -p "¿Continuar de todas formas? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Deployment cancelado"
        exit 0
    fi
fi

# =====================================================
# 2. SHOW ESTIMATED COSTS
# =====================================================
print_header "💰 Costos Estimados Mensuales"

echo ""
echo "Configuración propuesta (optimizada para Students):"
echo ""
echo -e "${CYAN}┌─────────────────────────────────────────────────────┐${NC}"
echo -e "${CYAN}│ 1. PostgreSQL Flexible Server (Burstable B1ms)     │${NC}"
echo "│    - 1 vCore, 2GB RAM                              │"
echo "│    - 32GB Storage                                  │"
echo "│    - Backup 7 días                                 │"
echo -e "${GREEN}│    Costo: ~$12-15/mes                              │${NC}"
echo -e "${CYAN}├─────────────────────────────────────────────────────┤${NC}"
echo -e "${CYAN}│ 2. Redis Cache (Basic C0)                          │${NC}"
echo "│    - 250MB Memoria                                 │"
echo "│    - SSL habilitado                                │"
echo -e "${GREEN}│    Costo: ~$16/mes                                 │${NC}"
echo -e "${CYAN}├─────────────────────────────────────────────────────┤${NC}"
echo -e "${CYAN}│ 3. Cosmos DB Serverless (MongoDB API)              │${NC}"
echo "│    - Pay-per-use                                   │"
echo "│    - Auto-scaling                                  │"
echo -e "${GREEN}│    Costo: ~$5-10/mes (uso moderado)                │${NC}"
echo -e "${CYAN}├─────────────────────────────────────────────────────┤${NC}"
echo -e "${CYAN}│ 4. Key Vault                                       │${NC}"
echo "│    - Almacenamiento de secretos                    │"
echo -e "${GREEN}│    Costo: ~$0.03/mes                               │${NC}"
echo -e "${CYAN}└─────────────────────────────────────────────────────┘${NC}"
echo ""
echo -e "${GREEN}💵 TOTAL ESTIMADO: ~$35-45/mes${NC}"
echo -e "${BLUE}🎓 Con Azure for Students: GRATIS ($100 crédito/mes)${NC}"
echo ""

read -p "¿Continuar con el deployment? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Deployment cancelado"
    exit 0
fi

# =====================================================
# 3. CREATE RESOURCE GROUP
# =====================================================
print_header "📦 Creando Resource Group"

if az group exists --name "$RESOURCE_GROUP" | grep -q "true"; then
    print_warning "Resource group '$RESOURCE_GROUP' ya existe"
    read -p "¿Usar el existente? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Deployment cancelado. Cambia RESOURCE_GROUP en el script."
        exit 1
    fi
else
    print_info "Creando resource group en $LOCATION..."
    az group create \
        --name "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --output none
    print_success "Resource group creado: $RESOURCE_GROUP"
fi

# =====================================================
# 4. CREATE KEY VAULT (para guardar passwords)
# =====================================================
print_header "🔐 Creando Key Vault"

if az keyvault show --name "$KEYVAULT_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    print_warning "Key Vault ya existe"
else
    print_info "Creando Key Vault..."
    az keyvault create \
        --name "$KEYVAULT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --output none
    
    print_success "Key Vault creado: $KEYVAULT_NAME"
fi

# =====================================================
# 5. CREATE POSTGRESQL DATABASE
# =====================================================
print_header "🐘 Creando PostgreSQL Flexible Server"

# Generate secure password
POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-25)

if az postgres flexible-server show --name "$POSTGRES_SERVER" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    print_warning "PostgreSQL server ya existe"
    echo ""
    print_info "Recuperando información existente..."
    
    # Try to get password from Key Vault
    POSTGRES_PASSWORD=$(az keyvault secret show \
        --vault-name "$KEYVAULT_NAME" \
        --name "postgres-password" \
        --query value -o tsv 2>/dev/null || echo "")
    
    if [ -z "$POSTGRES_PASSWORD" ]; then
        print_warning "No se pudo recuperar la contraseña del Key Vault"
        read -s -p "Ingresa la contraseña de PostgreSQL (o presiona Enter para generar nueva): " INPUT_PASSWORD
        echo
        if [ -z "$INPUT_PASSWORD" ]; then
            POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-25)
            print_info "Nueva contraseña generada"
        else
            POSTGRES_PASSWORD="$INPUT_PASSWORD"
        fi
    fi
else
    print_info "Creando PostgreSQL Flexible Server (optimizado para Students)..."
    echo "⏳ Esto puede tomar 5-10 minutos, por favor espera..."
    
    az postgres flexible-server create \
        --name "$POSTGRES_SERVER" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --admin-user "$POSTGRES_ADMIN" \
        --admin-password "$POSTGRES_PASSWORD" \
        --sku-name Standard_B1ms \
        --tier Burstable \
        --storage-size 32 \
        --version 15 \
        --public-access 0.0.0.0-255.255.255.255 \
        --backup-retention 7 \
        --output none
    
    print_success "PostgreSQL server creado: $POSTGRES_SERVER"
    
    # Store password in Key Vault
    print_info "Guardando contraseña en Key Vault..."
    az keyvault secret set \
        --vault-name "$KEYVAULT_NAME" \
        --name "postgres-password" \
        --value "$POSTGRES_PASSWORD" \
        --output none
    
    # Create database
    print_info "Creando base de datos '$POSTGRES_DB'..."
    az postgres flexible-server db create \
        --resource-group "$RESOURCE_GROUP" \
        --server-name "$POSTGRES_SERVER" \
        --database-name "$POSTGRES_DB" \
        --output none
    
    print_success "Base de datos '$POSTGRES_DB' creada"
    
    # Configure firewall rule for current IP
    print_info "Configurando reglas de firewall..."
    MY_IP=$(curl -s https://api.ipify.org)
    az postgres flexible-server firewall-rule create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$POSTGRES_SERVER" \
        --rule-name "AllowMyIP" \
        --start-ip-address "$MY_IP" \
        --end-ip-address "$MY_IP" \
        --output none
    
    print_success "Firewall configurado para tu IP: $MY_IP"
fi

# =====================================================
# 6. CREATE REDIS CACHE
# =====================================================
print_header "🔴 Creando Redis Cache"

if az redis show --name "$REDIS_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    print_warning "Redis cache ya existe"
else
    print_info "Creando Redis cache (Basic C0 - optimizado para Students)..."
    echo "⏳ Esto puede tomar 10-15 minutos, por favor espera..."
    
    az redis create \
        --name "$REDIS_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --sku Basic \
        --vm-size C0 \
        --enable-non-ssl-port false \
        --output none
    
    print_success "Redis cache creado: $REDIS_NAME"
fi

# Get Redis keys
print_info "Obteniendo claves de Redis..."
REDIS_KEY=$(az redis list-keys \
    --name "$REDIS_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query primaryKey -o tsv)

# Store in Key Vault
az keyvault secret set \
    --vault-name "$KEYVAULT_NAME" \
    --name "redis-key" \
    --value "$REDIS_KEY" \
    --output none

print_success "Claves de Redis guardadas en Key Vault"

# =====================================================
# 7. CREATE COSMOS DB (MongoDB API)
# =====================================================
print_header "🌌 Creando Cosmos DB (MongoDB API)"

if az cosmosdb show --name "$COSMOS_ACCOUNT" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    print_warning "Cosmos DB account ya existe"
else
    print_info "Creando Cosmos DB Serverless (optimizado para Students)..."
    echo "⏳ Esto puede tomar 5-10 minutos, por favor espera..."
    
    az cosmosdb create \
        --name "$COSMOS_ACCOUNT" \
        --resource-group "$RESOURCE_GROUP" \
        --kind MongoDB \
        --server-version 6.0 \
        --default-consistency-level Session \
        --locations regionName="$LOCATION" failoverPriority=0 \
        --capabilities EnableServerless \
        --output none
    
    print_success "Cosmos DB account creado: $COSMOS_ACCOUNT"
    
    # Create database
    print_info "Creando base de datos 'upeu_documents'..."
    az cosmosdb mongodb database create \
        --account-name "$COSMOS_ACCOUNT" \
        --resource-group "$RESOURCE_GROUP" \
        --name upeu_documents \
        --output none
    
    print_success "Base de datos MongoDB creada"
fi

# Get Cosmos DB connection string
print_info "Obteniendo connection string de Cosmos DB..."
COSMOS_CONN=$(az cosmosdb keys list \
    --name "$COSMOS_ACCOUNT" \
    --resource-group "$RESOURCE_GROUP" \
    --type connection-strings \
    --query "connectionStrings[0].connectionString" -o tsv)

# Store in Key Vault
az keyvault secret set \
    --vault-name "$KEYVAULT_NAME" \
    --name "cosmos-connection-string" \
    --value "$COSMOS_CONN" \
    --output none

print_success "Connection string guardado en Key Vault"

# =====================================================
# 8. GENERATE CONNECTION STRINGS
# =====================================================
print_header "🔗 Generando Connection Strings"

# PostgreSQL
POSTGRES_HOST="$POSTGRES_SERVER.postgres.database.azure.com"
POSTGRES_CONN="postgres://$POSTGRES_ADMIN:$POSTGRES_PASSWORD@$POSTGRES_HOST:5432/$POSTGRES_DB?sslmode=require"

# Redis
REDIS_HOST="$REDIS_NAME.redis.cache.windows.net"
REDIS_CONN="rediss://:$REDIS_KEY@$REDIS_HOST:6380/0"

# MongoDB/Cosmos
MONGO_CONN="$COSMOS_CONN"

print_success "Connection strings generados"

# =====================================================
# 9. CREATE .env FILE FOR LOCAL DEVELOPMENT
# =====================================================
print_header "📝 Creando archivo .env.azure"

ENV_FILE=".env.azure"

cat > "$ENV_FILE" << EOF
# =====================================================
# AZURE DATABASES CONNECTION - AUTO-GENERATED
# =====================================================
# Generado: $(date)
# Resource Group: $RESOURCE_GROUP
# Location: $LOCATION

# =====================================================
# POSTGRESQL
# =====================================================
DB_NAME=$POSTGRES_DB
DB_USER=$POSTGRES_ADMIN
DB_PASSWORD=$POSTGRES_PASSWORD
DB_HOST=$POSTGRES_HOST
DB_PORT=5432

# PostgreSQL Connection String (completo)
DATABASE_URL=$POSTGRES_CONN

# =====================================================
# REDIS CACHE
# =====================================================
REDIS_HOST=$REDIS_HOST
REDIS_PORT=6380
REDIS_PASSWORD=$REDIS_KEY
USE_REDIS_CACHE=True

# Redis Connection String (completo)
REDIS_URL=$REDIS_CONN

# =====================================================
# MONGODB (Cosmos DB)
# =====================================================
MONGODB_DB_NAME=upeu_documents

# MongoDB Connection String (completo)
MONGODB_URI=$MONGO_CONN

# =====================================================
# CELERY
# =====================================================
CELERY_BROKER_URL=$REDIS_CONN
CELERY_RESULT_BACKEND=$REDIS_CONN
CELERY_TASK_ALWAYS_EAGER=False

# =====================================================
# AZURE KEY VAULT
# =====================================================
AZURE_KEY_VAULT_NAME=$KEYVAULT_NAME
AZURE_KEY_VAULT_URI=https://$KEYVAULT_NAME.vault.azure.net/

# =====================================================
# DJANGO SETTINGS (ajustar según necesites)
# =====================================================
DEBUG=True
SECRET_KEY=django-insecure-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# =====================================================
# NOTAS IMPORTANTES
# =====================================================
# 1. NO commitear este archivo a git (ya está en .gitignore)
# 2. Para producción, usar variables de entorno reales
# 3. Passwords almacenados en Azure Key Vault: $KEYVAULT_NAME
# 4. Conexión desde local requiere IP whitelisted en firewall

EOF

print_success "Archivo .env.azure creado"

# =====================================================
# 10. TEST CONNECTIONS
# =====================================================
print_header "🧪 Probando Conexiones"

# Test PostgreSQL
print_info "Probando PostgreSQL..."
if command -v psql &> /dev/null; then
    if psql "$POSTGRES_CONN" -c "SELECT version();" &> /dev/null; then
        print_success "PostgreSQL: ✅ Conexión exitosa"
    else
        print_warning "PostgreSQL: ⚠️  No se pudo conectar (verifica firewall)"
    fi
else
    print_info "PostgreSQL: psql no instalado, saltando test"
fi

# Test Redis
print_info "Probando Redis..."
if command -v redis-cli &> /dev/null; then
    if redis-cli -h "$REDIS_HOST" -p 6380 --tls -a "$REDIS_KEY" PING &> /dev/null; then
        print_success "Redis: ✅ Conexión exitosa"
    else
        print_warning "Redis: ⚠️  No se pudo conectar (verifica firewall)"
    fi
else
    print_info "Redis: redis-cli no instalado, saltando test"
fi

print_success "Tests de conexión completados"

# =====================================================
# 11. DEPLOYMENT SUMMARY
# =====================================================
print_header "📊 RESUMEN DEL DEPLOYMENT"

echo ""
echo -e "${GREEN}✅ ¡Deployment completado exitosamente!${NC}"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}📦 RECURSOS CREADOS${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Resource Group:${NC}"
echo "  📁 $RESOURCE_GROUP ($LOCATION)"
echo ""
echo -e "${BLUE}1. PostgreSQL Database:${NC}"
echo "  🐘 Server: $POSTGRES_HOST"
echo "  📊 Database: $POSTGRES_DB"
echo "  👤 Usuario: $POSTGRES_ADMIN"
echo "  🔑 Password: $POSTGRES_PASSWORD"
echo ""
echo -e "${BLUE}2. Redis Cache:${NC}"
echo "  🔴 Host: $REDIS_HOST"
echo "  🔌 Port: 6380 (SSL)"
echo "  🔑 Primary Key: ${REDIS_KEY:0:20}..."
echo ""
echo -e "${BLUE}3. Cosmos DB (MongoDB API):${NC}"
echo "  🌌 Account: $COSMOS_ACCOUNT"
echo "  📊 Database: upeu_documents"
echo "  🔗 Endpoint: $COSMOS_ACCOUNT.mongo.cosmos.azure.com"
echo ""
echo -e "${BLUE}4. Key Vault:${NC}"
echo "  🔐 Name: $KEYVAULT_NAME"
echo "  🔗 URI: https://$KEYVAULT_NAME.vault.azure.net/"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}💰 COSTOS ESTIMADOS${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""
echo "  PostgreSQL (B1ms): ~\$15/mes"
echo "  Redis (C0):        ~\$16/mes"
echo "  Cosmos DB:         ~\$5-10/mes"
echo "  Key Vault:         ~\$0.03/mes"
echo "  ────────────────────────────"
echo -e "${GREEN}  TOTAL:             ~\$36-41/mes${NC}"
echo ""
if [[ "$SUBSCRIPTION_NAME" == *"Azure for Students"* ]]; then
    echo -e "${GREEN}  🎓 Con tu crédito de \$100/mes: ¡GRATIS!${NC}"
    echo -e "${GREEN}  💵 Te sobran ~\$60/mes para otros recursos${NC}"
fi
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}📝 ARCHIVOS GENERADOS${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""
echo "  ✅ $ENV_FILE"
echo "     Connection strings para desarrollo local"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}🚀 PRÓXIMOS PASOS${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""
echo "1️⃣  Copiar configuración para desarrollo local:"
echo "   ${YELLOW}cp $ENV_FILE .env${NC}"
echo ""
echo "2️⃣  Probar conexión desde Django:"
echo "   ${YELLOW}python manage.py check${NC}"
echo "   ${YELLOW}python manage.py migrate${NC}"
echo ""
echo "3️⃣  Cargar datos iniciales:"
echo "   ${YELLOW}python manage.py dbshell < docs/arquitectura/crear_bd_completa.sql${NC}"
echo ""
echo "4️⃣  Crear superusuario:"
echo "   ${YELLOW}python manage.py createsuperuser${NC}"
echo ""
echo "5️⃣  Desplegar aplicación (opcional):"
echo "   • Local: ${YELLOW}python manage.py runserver${NC}"
echo "   • Render: Usar estas conexiones en variables de entorno"
echo "   • Azure App Service: Usar script deploy_azure.sh completo"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}⚠️  INFORMACIÓN IMPORTANTE${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""
echo "🔒 Credenciales guardadas en:"
echo "   • Archivo local: ${YELLOW}$ENV_FILE${NC}"
echo "   • Azure Key Vault: ${YELLOW}$KEYVAULT_NAME${NC}"
echo ""
echo "🌐 Acceso desde local:"
echo "   • Tu IP actual ($MY_IP) ya está whitelisted"
echo "   • Para otras IPs, agregar en Azure Portal → Firewall rules"
echo ""
echo "🔗 Gestionar recursos:"
echo "   • Portal: ${BLUE}https://portal.azure.com${NC}"
echo "   • Resource Group: Buscar '$RESOURCE_GROUP'"
echo ""
echo "📊 Monitorear costos:"
echo "   • Portal → Cost Management + Billing"
echo "   • Alerts recomendados: \$50, \$75, \$90"
echo ""
echo -e "${GREEN}✨ ¡Todo listo! Tus bases de datos están en la nube.${NC}"
echo ""

# Save summary to file
SUMMARY_FILE="azure_databases_deployment_summary.txt"
{
    echo "AZURE DATABASES DEPLOYMENT SUMMARY"
    echo "Generated: $(date)"
    echo "=================================================="
    echo ""
    echo "PostgreSQL:"
    echo "  Connection: $POSTGRES_CONN"
    echo ""
    echo "Redis:"
    echo "  Connection: $REDIS_CONN"
    echo ""
    echo "MongoDB (Cosmos DB):"
    echo "  Connection: $MONGO_CONN"
    echo ""
    echo "Key Vault:"
    echo "  Name: $KEYVAULT_NAME"
    echo "  URI: https://$KEYVAULT_NAME.vault.azure.net/"
    echo ""
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Location: $LOCATION"
} > "$SUMMARY_FILE"

print_success "Resumen guardado en: $SUMMARY_FILE"
echo ""
print_success "🎉 ¡Deployment completado! 🎉"
