#!/bin/bash
# =====================================================
# AZURE DEPLOYMENT SCRIPT
# Sistema de Gestión de Prácticas Profesionales - UPeU
# =====================================================
# Este script automatiza el despliegue completo a Azure
# Requiere: Azure CLI instalado y autenticado

set -e  # Exit on error

# =====================================================
# CONFIGURATION
# =====================================================
RESOURCE_GROUP="rg-upeu-ppp"
LOCATION="eastus"
APP_SERVICE_PLAN="plan-upeu-production"
WEBAPP_NAME="app-upeu-ppp"
POSTGRES_SERVER="psql-upeu-ppp"
POSTGRES_DB="upeu_ppp_system"
POSTGRES_ADMIN="upeu_admin"
REDIS_NAME="redis-upeu-ppp"
COSMOS_ACCOUNT="cosmos-upeu-ppp"
STORAGE_ACCOUNT="stupeufiles"
KEYVAULT_NAME="kv-upeu-ppp"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =====================================================
# HELPER FUNCTIONS
# =====================================================
print_header() {
    echo -e "${BLUE}========================================"
    echo -e "$1"
    echo -e "========================================${NC}"
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

# =====================================================
# CHECK PREREQUISITES
# =====================================================
print_header "🔍 Checking Prerequisites"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Install from: https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi
print_success "Azure CLI found"

# Check if logged in
if ! az account show &> /dev/null; then
    print_warning "Not logged in to Azure. Logging in..."
    az login
fi
print_success "Azure authentication verified"

# Get subscription info
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
echo -e "Using subscription: ${GREEN}$SUBSCRIPTION_NAME${NC} ($SUBSCRIPTION_ID)"

# =====================================================
# CONFIRM DEPLOYMENT
# =====================================================
echo ""
print_warning "This will create the following Azure resources:"
echo "  - Resource Group: $RESOURCE_GROUP"
echo "  - App Service Plan: $APP_SERVICE_PLAN (P1V3 - ~\$100/month)"
echo "  - Web App: $WEBAPP_NAME"
echo "  - PostgreSQL Server: $POSTGRES_SERVER (~\$110/month)"
echo "  - Redis Cache: $REDIS_NAME (~\$75/month)"
echo "  - Cosmos DB: $COSMOS_ACCOUNT (~\$25/month)"
echo "  - Storage Account: $STORAGE_ACCOUNT (~\$5/month)"
echo "  - Key Vault: $KEYVAULT_NAME (~\$0.03/month)"
echo ""
echo -e "${YELLOW}Estimated monthly cost: ~\$315-365${NC}"
echo ""
read -p "Continue with deployment? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled"
    exit 0
fi

# =====================================================
# 1. CREATE RESOURCE GROUP
# =====================================================
print_header "📦 Creating Resource Group"

if az group exists --name "$RESOURCE_GROUP" | grep -q "true"; then
    print_warning "Resource group already exists"
else
    az group create \
        --name "$RESOURCE_GROUP" \
        --location "$LOCATION"
    print_success "Resource group created: $RESOURCE_GROUP"
fi

# =====================================================
# 2. CREATE APP SERVICE PLAN
# =====================================================
print_header "🏗️  Creating App Service Plan"

if az appservice plan show --name "$APP_SERVICE_PLAN" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    print_warning "App Service Plan already exists"
else
    az appservice plan create \
        --name "$APP_SERVICE_PLAN" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --sku P1V3 \
        --is-linux
    print_success "App Service Plan created"
fi

# =====================================================
# 3. CREATE WEB APP
# =====================================================
print_header "🌐 Creating Web App"

if az webapp show --name "$WEBAPP_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    print_warning "Web App already exists"
else
    az webapp create \
        --name "$WEBAPP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --plan "$APP_SERVICE_PLAN" \
        --runtime "PYTHON:3.11"
    print_success "Web App created: https://$WEBAPP_NAME.azurewebsites.net"
fi

# =====================================================
# 4. CREATE POSTGRESQL DATABASE
# =====================================================
print_header "🐘 Creating PostgreSQL Database"

# Generate secure password
POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-20)

if az postgres flexible-server show --name "$POSTGRES_SERVER" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    print_warning "PostgreSQL server already exists"
else
    echo "Creating PostgreSQL Flexible Server (this may take 5-10 minutes)..."
    az postgres flexible-server create \
        --name "$POSTGRES_SERVER" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --admin-user "$POSTGRES_ADMIN" \
        --admin-password "$POSTGRES_PASSWORD" \
        --sku-name Standard_D2s_v3 \
        --tier GeneralPurpose \
        --storage-size 128 \
        --version 15 \
        --public-access 0.0.0.0
    
    print_success "PostgreSQL server created"
    echo -e "${YELLOW}PostgreSQL Password: $POSTGRES_PASSWORD${NC}"
    echo -e "${RED}SAVE THIS PASSWORD! You won't see it again.${NC}"
    
    # Create database
    az postgres flexible-server db create \
        --resource-group "$RESOURCE_GROUP" \
        --server-name "$POSTGRES_SERVER" \
        --database-name "$POSTGRES_DB"
    
    print_success "Database '$POSTGRES_DB' created"
fi

# =====================================================
# 5. CREATE REDIS CACHE
# =====================================================
print_header "🔴 Creating Redis Cache"

if az redis show --name "$REDIS_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    print_warning "Redis cache already exists"
else
    echo "Creating Redis cache (this may take 10-15 minutes)..."
    az redis create \
        --name "$REDIS_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --sku Standard \
        --vm-size C1 \
        --enable-non-ssl-port false
    
    print_success "Redis cache created"
fi

# Get Redis keys
REDIS_KEY=$(az redis list-keys --name "$REDIS_NAME" --resource-group "$RESOURCE_GROUP" --query primaryKey -o tsv)
print_success "Redis key retrieved"

# =====================================================
# 6. CREATE COSMOS DB (MongoDB API)
# =====================================================
print_header "🌌 Creating Cosmos DB"

if az cosmosdb show --name "$COSMOS_ACCOUNT" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    print_warning "Cosmos DB account already exists"
else
    echo "Creating Cosmos DB account (this may take 5-10 minutes)..."
    az cosmosdb create \
        --name "$COSMOS_ACCOUNT" \
        --resource-group "$RESOURCE_GROUP" \
        --kind MongoDB \
        --server-version 6.0 \
        --default-consistency-level Session \
        --locations regionName="$LOCATION" failoverPriority=0
    
    print_success "Cosmos DB account created"
    
    # Create database
    az cosmosdb mongodb database create \
        --account-name "$COSMOS_ACCOUNT" \
        --resource-group "$RESOURCE_GROUP" \
        --name upeu_documents
    
    print_success "MongoDB database created"
fi

# Get Cosmos DB connection string
COSMOS_CONN=$(az cosmosdb keys list --name "$COSMOS_ACCOUNT" --resource-group "$RESOURCE_GROUP" --type connection-strings --query "connectionStrings[0].connectionString" -o tsv)
print_success "Cosmos DB connection string retrieved"

# =====================================================
# 7. CREATE STORAGE ACCOUNT
# =====================================================
print_header "💾 Creating Storage Account"

if az storage account show --name "$STORAGE_ACCOUNT" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    print_warning "Storage account already exists"
else
    az storage account create \
        --name "$STORAGE_ACCOUNT" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --sku Standard_LRS
    
    print_success "Storage account created"
    
    # Create containers
    STORAGE_KEY=$(az storage account keys list --account-name "$STORAGE_ACCOUNT" --resource-group "$RESOURCE_GROUP" --query "[0].value" -o tsv)
    
    az storage container create --name static --account-name "$STORAGE_ACCOUNT" --account-key "$STORAGE_KEY" --public-access blob
    az storage container create --name media --account-name "$STORAGE_ACCOUNT" --account-key "$STORAGE_KEY" --public-access blob
    az storage container create --name backups --account-name "$STORAGE_ACCOUNT" --account-key "$STORAGE_KEY"
    
    print_success "Storage containers created"
fi

STORAGE_CONN=$(az storage account show-connection-string --name "$STORAGE_ACCOUNT" --resource-group "$RESOURCE_GROUP" --query connectionString -o tsv)
print_success "Storage connection string retrieved"

# =====================================================
# 8. CREATE KEY VAULT
# =====================================================
print_header "🔐 Creating Key Vault"

if az keyvault show --name "$KEYVAULT_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    print_warning "Key Vault already exists"
else
    az keyvault create \
        --name "$KEYVAULT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION"
    
    print_success "Key Vault created"
fi

# Generate Django secret key
DJANGO_SECRET=$(openssl rand -base64 64 | tr -d "\n")

# Store secrets in Key Vault
az keyvault secret set --vault-name "$KEYVAULT_NAME" --name SECRET-KEY --value "$DJANGO_SECRET"
az keyvault secret set --vault-name "$KEYVAULT_NAME" --name DB-PASSWORD --value "$POSTGRES_PASSWORD"
az keyvault secret set --vault-name "$KEYVAULT_NAME" --name REDIS-KEY --value "$REDIS_KEY"

print_success "Secrets stored in Key Vault"

# =====================================================
# 9. CONFIGURE WEB APP
# =====================================================
print_header "⚙️  Configuring Web App"

# Enable managed identity
az webapp identity assign \
    --name "$WEBAPP_NAME" \
    --resource-group "$RESOURCE_GROUP"

PRINCIPAL_ID=$(az webapp identity show --name "$WEBAPP_NAME" --resource-group "$RESOURCE_GROUP" --query principalId -o tsv)

# Grant Key Vault access
az keyvault set-policy \
    --name "$KEYVAULT_NAME" \
    --object-id "$PRINCIPAL_ID" \
    --secret-permissions get list

print_success "Managed identity configured"

# Configure app settings
DATABASE_URL="postgres://$POSTGRES_ADMIN:$POSTGRES_PASSWORD@$POSTGRES_SERVER.postgres.database.azure.com:5432/$POSTGRES_DB?sslmode=require"
REDIS_URL="rediss://:$REDIS_KEY@$REDIS_NAME.redis.cache.windows.net:6380/0"

az webapp config appsettings set \
    --name "$WEBAPP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings \
        DJANGO_SETTINGS_MODULE="config.settings" \
        DEBUG="False" \
        SECRET_KEY="@Microsoft.KeyVault(SecretUri=https://$KEYVAULT_NAME.vault.azure.net/secrets/SECRET-KEY/)" \
        ALLOWED_HOSTS="$WEBAPP_NAME.azurewebsites.net" \
        DATABASE_URL="$DATABASE_URL" \
        REDIS_URL="$REDIS_URL" \
        MONGODB_URI="$COSMOS_CONN" \
        AZURE_STORAGE_CONNECTION_STRING="$STORAGE_CONN" \
        USE_REDIS_CACHE="True" \
        CELERY_BROKER_URL="$REDIS_URL" \
        CELERY_RESULT_BACKEND="$REDIS_URL" \
        CELERY_TASK_ALWAYS_EAGER="False" \
        SESSION_COOKIE_SECURE="True" \
        CSRF_COOKIE_SECURE="True" \
        SECURE_SSL_REDIRECT="True"

print_success "App settings configured"

# Set startup command
az webapp config set \
    --name "$WEBAPP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --startup-file "bash startup.sh"

print_success "Startup command configured"

# =====================================================
# 10. DEPLOY APPLICATION
# =====================================================
print_header "🚀 Deploying Application"

# Create deployment package
echo "Creating deployment package..."
git archive -o app.zip HEAD

# Deploy
echo "Uploading to Azure..."
az webapp deployment source config-zip \
    --name "$WEBAPP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --src app.zip

rm app.zip

print_success "Application deployed"

# =====================================================
# 11. DEPLOYMENT SUMMARY
# =====================================================
print_header "📊 Deployment Summary"

echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo "Resources created:"
echo "  - Resource Group: $RESOURCE_GROUP"
echo "  - Web App: https://$WEBAPP_NAME.azurewebsites.net"
echo "  - PostgreSQL: $POSTGRES_SERVER.postgres.database.azure.com"
echo "  - Redis: $REDIS_NAME.redis.cache.windows.net"
echo "  - Cosmos DB: $COSMOS_ACCOUNT.mongo.cosmos.azure.com"
echo "  - Storage: $STORAGE_ACCOUNT.blob.core.windows.net"
echo "  - Key Vault: https://$KEYVAULT_NAME.vault.azure.net"
echo ""
echo -e "${YELLOW}Important credentials (save these):${NC}"
echo "  - PostgreSQL admin: $POSTGRES_ADMIN"
echo "  - PostgreSQL password: $POSTGRES_PASSWORD"
echo "  - Django secret key: Stored in Key Vault"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Configure custom domain (if needed)"
echo "  2. Set up GitHub Actions for CI/CD"
echo "  3. Configure monitoring in Application Insights"
echo "  4. Review and adjust scaling settings"
echo "  5. Test the deployment: curl https://$WEBAPP_NAME.azurewebsites.net/api/health/"
echo ""
print_success "All done! 🎉"
