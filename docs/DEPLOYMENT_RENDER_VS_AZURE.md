# 🚀 Guía Completa de Despliegue: Render vs Azure

## 📊 Comparativa Rápida

| Característica | **Render** | **Azure** |
|----------------|------------|-----------|
| **Complejidad** | ⭐⭐ Baja | ⭐⭐⭐⭐ Alta |
| **Configuración inicial** | 15-30 minutos | 2-4 horas |
| **Costo mensual (estimado)** | $25-$100 | $200-$500+ |
| **Escalabilidad** | Buena | Excelente |
| **Soporte** | Básico | Empresarial |
| **Ideal para** | Proyectos académicos, startups | Empresas, producción crítica |
| **CI/CD integrado** | ✅ Automático | ⚠️ Requiere configuración |
| **Bases de datos incluidas** | PostgreSQL, Redis | Requiere configuración separada |

---

# 🎨 Opción 1: RENDER (Recomendado para tu proyecto académico)

## ✅ Ventajas para tu caso
- ✅ **Gratis para empezar** (tier gratuito limitado)
- ✅ **Configuración simple** con Git
- ✅ **PostgreSQL y Redis incluidos**
- ✅ **SSL/HTTPS automático**
- ✅ **Despliegue automático** desde GitHub
- ✅ **Ideal para proyectos de graduación**

## 📋 Lo que necesitas en Render

### **1. Cuenta y Servicios**

#### Crear cuenta:
1. Ve a [render.com](https://render.com)
2. Regístrate con tu cuenta de GitHub
3. Conecta tu repositorio `DJGRedis.PA`

#### Servicios a crear (5 servicios):

##### **A) Web Service - Django Application**
```yaml
Name: upeu-ppp-backend
Environment: Python 3.11
Build Command: pip install -r requirements/production.txt
Start Command: gunicorn --bind 0.0.0.0:$PORT config.wsgi:application
Plan: Starter ($7/mes) o Free (con limitaciones)
```

##### **B) PostgreSQL Database**
```yaml
Name: upeu-postgres
Plan: Starter ($7/mes) - 256MB RAM, 1GB Storage
Version: PostgreSQL 15
```

##### **C) Redis**
```yaml
Name: upeu-redis
Plan: Starter ($7/mes) - 100MB memoria
```

##### **D) Celery Worker**
```yaml
Name: upeu-celery-worker
Build Command: pip install -r requirements/production.txt
Start Command: celery -A config worker --loglevel=info
Plan: Starter ($7/mes)
```

##### **E) Celery Beat**
```yaml
Name: upeu-celery-beat
Build Command: pip install -r requirements/production.txt
Start Command: celery -A config beat --loglevel=info
Plan: Starter ($7/mes)
```

**Costo total mensual**: ~$35-45 USD

---

### **2. Configuración de Variables de Entorno**

En **cada servicio** de Render, agregar estas variables:

```bash
# Django Core
SECRET_KEY=tu-secreto-super-seguro-generado-random-64-caracteres
DEBUG=False
ALLOWED_HOSTS=upeu-ppp-backend.onrender.com,tu-dominio.com
DJANGO_SETTINGS_MODULE=config.settings

# Database (autorellenado por Render)
DATABASE_URL=postgres://user:pass@host:5432/dbname
DB_NAME=upeu_ppp_system
DB_USER=upeu_admin
DB_PASSWORD=<generado por Render>
DB_HOST=<generado por Render>
DB_PORT=5432

# Redis (autorellenado por Render)
REDIS_URL=redis://:<password>@<host>:6379
USE_REDIS_CACHE=True

# Celery
CELERY_BROKER_URL=$REDIS_URL
CELERY_RESULT_BACKEND=$REDIS_URL
CELERY_TASK_ALWAYS_EAGER=False
CELERY_TIMEZONE=America/Lima

# MongoDB (usar MongoDB Atlas - Free tier)
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/upeu_documents
MONGODB_DB_NAME=upeu_documents

# Email (usar Gmail o SendGrid)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password

# Security
ALLOWED_EMAIL_DOMAINS=upeu.edu.pe
AXES_FAILURE_LIMIT=5
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True

# CORS (ajustar según tu frontend)
CORS_ALLOWED_ORIGINS=https://tu-frontend.com
CORS_ALLOW_CREDENTIALS=True

# Static/Media Files
STATIC_URL=/static/
MEDIA_URL=/media/
```

---

### **3. Archivos necesarios en tu repositorio**

#### **A) `render.yaml` (Blueprint - opcional pero recomendado)**

Crear en la raíz del proyecto:

```yaml
# render.yaml - Configuración Blueprint para Render
services:
  # Django Web Application
  - type: web
    name: upeu-ppp-backend
    env: python
    buildCommand: pip install -r requirements/production.txt && python manage.py collectstatic --noinput && python manage.py migrate
    startCommand: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 config.wsgi:application
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: DATABASE_URL
        fromDatabase:
          name: upeu-postgres
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: upeu-redis
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: False
      - key: DJANGO_SETTINGS_MODULE
        value: config.settings

  # Celery Worker
  - type: worker
    name: upeu-celery-worker
    env: python
    buildCommand: pip install -r requirements/production.txt
    startCommand: celery -A config worker --loglevel=info --concurrency=2
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: upeu-postgres
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: upeu-redis
          property: connectionString

  # Celery Beat
  - type: worker
    name: upeu-celery-beat
    env: python
    buildCommand: pip install -r requirements/production.txt
    startCommand: celery -A config beat --loglevel=info
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: upeu-postgres
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: upeu-redis
          property: connectionString

# Databases
databases:
  - name: upeu-postgres
    databaseName: upeu_ppp_system
    user: upeu_admin
    plan: starter

# Redis
  - type: redis
    name: upeu-redis
    plan: starter
    maxmemoryPolicy: allkeys-lru
```

#### **B) `build.sh` (Script de construcción)**

Crear en la raíz:

```bash
#!/usr/bin/env bash
# build.sh - Script de construcción para Render

set -o errexit  # Exit on error

echo "🔨 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements/production.txt

echo "📦 Collecting static files..."
python manage.py collectstatic --no-input

echo "🗄️  Running database migrations..."
python manage.py migrate --no-input

echo "✅ Build completed successfully!"
```

Hacer ejecutable:
```bash
chmod +x build.sh
```

#### **C) `Procfile` (Opcional - si no usas render.yaml)**

```procfile
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2
worker: celery -A config worker --loglevel=info
beat: celery -A config beat --loglevel=info
```

---

### **4. MongoDB - Usar MongoDB Atlas (Gratis)**

Como Render no ofrece MongoDB nativo, usar **MongoDB Atlas**:

1. Ve a [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Crea cuenta gratuita
3. Crea un cluster M0 (FREE TIER - 512MB)
4. Configura:
   - Database name: `upeu_documents`
   - Username: `upeu_admin`
   - Password: `<genera una segura>`
5. Whitelist IP: `0.0.0.0/0` (permitir desde cualquier lugar)
6. Obtén tu connection string:
   ```
   mongodb+srv://upeu_admin:<password>@cluster0.xxxxx.mongodb.net/upeu_documents
   ```
7. Agrega `MONGODB_URI` en variables de entorno de Render

---

### **5. Configuración de Dominio Personalizado**

En Render (opcional):
1. Ve a **Settings** → **Custom Domains**
2. Agrega tu dominio: `practicas.upeu.edu.pe`
3. Configura DNS en tu registrador:
   ```
   CNAME: practicas → upeu-ppp-backend.onrender.com
   ```

---

### **6. Pasos de Despliegue**

#### **Despliegue automático (con render.yaml):**

1. **Conectar repositorio**:
   - Dashboard Render → **New** → **Blueprint**
   - Seleccionar repositorio `DJGRedis.PA`
   - Render detecta automáticamente `render.yaml`

2. **Aplicar configuración**:
   - Revisar servicios a crear
   - Click **Apply**

3. **Configurar variables secretas**:
   - Ir a cada servicio
   - Agregar variables faltantes (EMAIL, MONGODB, etc.)

4. **Iniciar despliegue**:
   - Render automáticamente construye y despliega
   - Monitorea logs en tiempo real

#### **Despliegue manual:**

1. **Crear PostgreSQL Database**:
   ```
   Dashboard → New → PostgreSQL
   Name: upeu-postgres
   Plan: Starter
   ```

2. **Crear Redis**:
   ```
   Dashboard → New → Redis
   Name: upeu-redis
   Plan: Starter
   ```

3. **Crear Web Service**:
   ```
   Dashboard → New → Web Service
   Connect Repository: DJGRedis.PA
   Name: upeu-ppp-backend
   Build Command: pip install -r requirements/production.txt
   Start Command: gunicorn config.wsgi:application
   Environment Variables: (agregar todas las listadas arriba)
   ```

4. **Crear Celery Worker**:
   ```
   Dashboard → New → Background Worker
   Name: upeu-celery-worker
   Build Command: pip install -r requirements/production.txt
   Start Command: celery -A config worker --loglevel=info
   ```

5. **Crear Celery Beat**:
   ```
   Dashboard → New → Background Worker
   Name: upeu-celery-beat
   Build Command: pip install -r requirements/production.txt
   Start Command: celery -A config beat --loglevel=info
   ```

---

### **7. Verificación Post-Despliegue**

```bash
# 1. Health check
curl https://upeu-ppp-backend.onrender.com/api/health/

# 2. Verificar admin
curl https://upeu-ppp-backend.onrender.com/admin/

# 3. Verificar API
curl https://upeu-ppp-backend.onrender.com/api/swagger/

# 4. Test GraphQL
curl https://upeu-ppp-backend.onrender.com/graphql/
```

---

### **8. Limitaciones de Render Free Tier**

⚠️ **Limitaciones del tier gratuito**:
- **Sleep después de 15 min** de inactividad
- **750 horas/mes** de uso
- **100GB de bandwidth**
- **Sin Celery** (solo 1 servicio web)
- **PostgreSQL limitado** a 90 días

💡 **Recomendación**: Usar **Starter Plan ($7/servicio)** para proyecto serio

---

### **9. Troubleshooting Render**

#### **Problema: App no inicia**
```bash
# Revisar logs en Dashboard
# Verificar que requirements.txt instala correctamente
pip freeze > requirements/production.txt
```

#### **Problema: Error de base de datos**
```bash
# Verificar DATABASE_URL en variables de entorno
# Ejecutar migraciones manualmente desde Shell:
python manage.py migrate
```

#### **Problema: Static files no cargan**
```bash
# Agregar en settings.py:
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# En middleware agregar:
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Agregar aquí
    ...
]
```

---

# ☁️ Opción 2: MICROSOFT AZURE (Producción Empresarial)

## ✅ Ventajas para proyecto profesional
- ✅ **Escalabilidad empresarial** ilimitada
- ✅ **Alta disponibilidad** (99.95% SLA)
- ✅ **Seguridad avanzada** (compliance, auditoría)
- ✅ **Soporte 24/7** (con plan premium)
- ✅ **Integración con AD** (Azure Active Directory)
- ✅ **Backup automático** y disaster recovery

## 📋 Lo que necesitas en Azure

### **1. Cuenta Azure**

#### Opciones de cuenta:
1. **Azure for Students**: $100 USD de crédito gratis (requiere email .edu)
   - Link: [azure.microsoft.com/students](https://azure.microsoft.com/es-es/free/students/)
   
2. **Free Trial**: $200 USD crédito por 30 días
   - Link: [azure.microsoft.com/free](https://azure.microsoft.com/es-es/free/)

3. **Pay-as-you-go**: Pago por uso real

---

### **2. Servicios Azure Necesarios**

#### **Arquitectura propuesta:**

```
┌─────────────────────────────────────────────────┐
│         Azure Front Door (CDN + WAF)           │
│         - SSL/TLS                              │
│         - DDoS protection                      │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│      Azure App Service Plan (P1V3)            │
│                                                 │
│  ┌───────────────┐  ┌───────────────┐         │
│  │ App Service 1 │  │ App Service 2 │  ...    │
│  │ Django + DRF  │  │ Django + DRF  │         │
│  └───────────────┘  └───────────────┘         │
└─────────────────────────────────────────────────┘
           │           │           │
    ┌──────┴───────┬───┴────┬──────┴─────┐
    │              │        │            │
┌───▼────┐  ┌─────▼──┐  ┌──▼───┐  ┌────▼─────┐
│Postgres│  │  Redis │  │Cosmos│  │   Blob   │
│Database│  │  Cache │  │  DB  │  │ Storage  │
└────────┘  └────────┘  └──────┘  └──────────┘
```

---

### **A) Azure App Service (Django)**

**Servicio**: Web App for Containers o Python Web App

**Configuración recomendada**:
```yaml
Resource Group: rg-upeu-ppp
App Service Plan: 
  Name: plan-upeu-production
  Tier: P1V3 (Premium)
  OS: Linux
  
App Service:
  Name: app-upeu-ppp
  Runtime: Python 3.11
  Region: East US o Brazil South (más cercano)
  
Specs:
  - 2 vCores
  - 8 GB RAM
  - Auto-scaling: 2-5 instancias
```

**Costo**: ~$100-150/mes

**Comandos Azure CLI**:
```bash
# Login
az login

# Crear resource group
az group create --name rg-upeu-ppp --location eastus

# Crear App Service Plan
az appservice plan create \
  --name plan-upeu-production \
  --resource-group rg-upeu-ppp \
  --sku P1V3 \
  --is-linux

# Crear Web App
az webapp create \
  --name app-upeu-ppp \
  --resource-group rg-upeu-ppp \
  --plan plan-upeu-production \
  --runtime "PYTHON:3.11"

# Configurar deployment desde GitHub
az webapp deployment source config \
  --name app-upeu-ppp \
  --resource-group rg-upeu-ppp \
  --repo-url https://github.com/AaronAP1/DJGRedis.PA \
  --branch master \
  --manual-integration
```

---

### **B) Azure Database for PostgreSQL**

**Configuración**:
```yaml
Service: Azure Database for PostgreSQL Flexible Server
Name: psql-upeu-ppp
Tier: General Purpose
Compute: Standard_D2s_v3 (2 vCores, 8GB RAM)
Storage: 128 GB SSD
Version: PostgreSQL 15
Backup: 
  - Retention: 30 días
  - Geo-redundant: Enabled
High Availability: Zone-redundant
```

**Costo**: ~$100-120/mes

**Comandos**:
```bash
# Crear PostgreSQL
az postgres flexible-server create \
  --name psql-upeu-ppp \
  --resource-group rg-upeu-ppp \
  --location eastus \
  --admin-user upeu_admin \
  --admin-password 'TuPasswordSeguro123!' \
  --sku-name Standard_D2s_v3 \
  --tier GeneralPurpose \
  --storage-size 128 \
  --version 15

# Configurar firewall (permitir Azure services)
az postgres flexible-server firewall-rule create \
  --name psql-upeu-ppp \
  --resource-group rg-upeu-ppp \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# Crear base de datos
az postgres flexible-server db create \
  --resource-group rg-upeu-ppp \
  --server-name psql-upeu-ppp \
  --database-name upeu_ppp_system
```

**Connection String**:
```
postgres://upeu_admin@psql-upeu-ppp:password@psql-upeu-ppp.postgres.database.azure.com:5432/upeu_ppp_system?sslmode=require
```

---

### **C) Azure Cache for Redis**

**Configuración**:
```yaml
Service: Azure Cache for Redis
Name: redis-upeu-ppp
Tier: Basic C1 (o Standard C1 para producción)
Cache Size: 1 GB
Version: Redis 6
SSL: Enabled
Port: 6380 (SSL), 6379 (non-SSL)
```

**Costo**: 
- Basic C1: ~$20/mes
- Standard C1: ~$75/mes (recomendado para producción)

**Comandos**:
```bash
# Crear Redis Cache
az redis create \
  --name redis-upeu-ppp \
  --resource-group rg-upeu-ppp \
  --location eastus \
  --sku Basic \
  --vm-size C1 \
  --enable-non-ssl-port false

# Obtener connection string
az redis list-keys \
  --name redis-upeu-ppp \
  --resource-group rg-upeu-ppp
```

**Connection String**:
```
rediss://:<primary-key>@redis-upeu-ppp.redis.cache.windows.net:6380/0
```

---

### **D) Azure Cosmos DB (MongoDB API)**

**Configuración**:
```yaml
Service: Azure Cosmos DB for MongoDB
Account Name: cosmos-upeu-ppp
API: MongoDB
Capacity Mode: Serverless (o Provisioned)
Consistency: Session
Geo-Replication: Optional
```

**Costo**: 
- Serverless: ~$0.25/millón de operaciones
- Provisioned 400 RU/s: ~$24/mes

**Comandos**:
```bash
# Crear Cosmos DB Account (MongoDB API)
az cosmosdb create \
  --name cosmos-upeu-ppp \
  --resource-group rg-upeu-ppp \
  --kind MongoDB \
  --server-version 6.0 \
  --default-consistency-level Session \
  --locations regionName=eastus failoverPriority=0

# Crear database
az cosmosdb mongodb database create \
  --account-name cosmos-upeu-ppp \
  --resource-group rg-upeu-ppp \
  --name upeu_documents

# Obtener connection string
az cosmosdb keys list \
  --name cosmos-upeu-ppp \
  --resource-group rg-upeu-ppp \
  --type connection-strings
```

**Connection String**:
```
mongodb://cosmos-upeu-ppp:<primary-key>@cosmos-upeu-ppp.mongo.cosmos.azure.com:10255/upeu_documents?ssl=true&replicaSet=globaldb&retrywrites=false
```

---

### **E) Azure Blob Storage (Archivos estáticos/media)**

**Configuración**:
```yaml
Service: Storage Account
Name: stupeufiles
Performance: Standard
Replication: LRS (Locally-redundant)
Containers:
  - static
  - media
  - backups
```

**Costo**: ~$2-5/mes

**Comandos**:
```bash
# Crear Storage Account
az storage account create \
  --name stupeufiles \
  --resource-group rg-upeu-ppp \
  --location eastus \
  --sku Standard_LRS

# Crear containers
az storage container create \
  --name static \
  --account-name stupeufiles \
  --public-access blob

az storage container create \
  --name media \
  --account-name stupeufiles \
  --public-access blob

# Obtener connection string
az storage account show-connection-string \
  --name stupeufiles \
  --resource-group rg-upeu-ppp
```

**Connection String**:
```
DefaultEndpointsProtocol=https;AccountName=stupeufiles;AccountKey=<key>;EndpointSuffix=core.windows.net
```

---

### **F) Azure Key Vault (Secretos)**

**Configuración**:
```yaml
Service: Key Vault
Name: kv-upeu-ppp
Pricing Tier: Standard
Soft Delete: Enabled (90 días)
Purge Protection: Enabled
```

**Costo**: ~$0.03/10,000 operaciones (casi gratis)

**Comandos**:
```bash
# Crear Key Vault
az keyvault create \
  --name kv-upeu-ppp \
  --resource-group rg-upeu-ppp \
  --location eastus

# Agregar secretos
az keyvault secret set \
  --vault-name kv-upeu-ppp \
  --name SECRET-KEY \
  --value 'tu-secreto-django-super-seguro'

az keyvault secret set \
  --vault-name kv-upeu-ppp \
  --name DB-PASSWORD \
  --value 'TuPasswordSeguro123!'

# Dar acceso a App Service
az webapp identity assign \
  --name app-upeu-ppp \
  --resource-group rg-upeu-ppp

# Obtener Principal ID
PRINCIPAL_ID=$(az webapp identity show \
  --name app-upeu-ppp \
  --resource-group rg-upeu-ppp \
  --query principalId -o tsv)

# Asignar permisos
az keyvault set-policy \
  --name kv-upeu-ppp \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get list
```

---

### **3. Variables de Entorno en Azure**

#### **Configurar Application Settings en App Service**:

```bash
# Via Azure CLI
az webapp config appsettings set \
  --name app-upeu-ppp \
  --resource-group rg-upeu-ppp \
  --settings \
    DJANGO_SETTINGS_MODULE="config.settings" \
    DEBUG="False" \
    SECRET_KEY="@Microsoft.KeyVault(SecretUri=https://kv-upeu-ppp.vault.azure.net/secrets/SECRET-KEY/)" \
    ALLOWED_HOSTS="app-upeu-ppp.azurewebsites.net,practicas.upeu.edu.pe" \
    DATABASE_URL="postgres://upeu_admin@psql-upeu-ppp:password@psql-upeu-ppp.postgres.database.azure.com:5432/upeu_ppp_system?sslmode=require" \
    REDIS_URL="rediss://:<primary-key>@redis-upeu-ppp.redis.cache.windows.net:6380/0" \
    MONGODB_URI="mongodb://cosmos-upeu-ppp:<key>@cosmos-upeu-ppp.mongo.cosmos.azure.com:10255/upeu_documents?ssl=true" \
    AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=stupeufiles;..." \
    USE_REDIS_CACHE="True" \
    CELERY_BROKER_URL="$REDIS_URL" \
    CELERY_RESULT_BACKEND="$REDIS_URL"
```

#### **Via Portal Azure**:
1. Portal → App Service → `app-upeu-ppp`
2. **Configuration** → **Application settings**
3. Click **+ New application setting**
4. Agregar cada variable

---

### **4. Deployment en Azure**

#### **Opción A: Deployment Center (GitHub Actions - Recomendado)**

1. **Portal Azure** → App Service → **Deployment Center**
2. **Source**: GitHub
3. **Organization**: AaronAP1
4. **Repository**: DJGRedis.PA
5. **Branch**: master
6. Azure crea automáticamente workflow `.github/workflows/azure-app-service.yml`

**Workflow generado**:
```yaml
name: Deploy to Azure App Service

on:
  push:
    branches:
      - master
  workflow_dispatch:

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements/production.txt

    - name: Collect static files
      run: python manage.py collectstatic --noinput

    - name: Run tests
      run: pytest

    - name: Deploy to Azure Web App
      uses: azure/webapps-deploy@v2
      with:
        app-name: 'app-upeu-ppp'
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
        package: .
```

#### **Opción B: Azure CLI Deployment**

```bash
# Desde tu máquina local
cd /path/to/DJGRedis.PA

# Login
az login

# Crear ZIP del proyecto
git archive -o app.zip HEAD

# Deploy
az webapp deployment source config-zip \
  --name app-upeu-ppp \
  --resource-group rg-upeu-ppp \
  --src app.zip
```

#### **Opción C: Docker Container (Avanzado)**

```bash
# Build Docker image
docker build -t upeu-ppp:latest .

# Tag para Azure Container Registry
docker tag upeu-ppp:latest upeuacr.azurecr.io/upeu-ppp:latest

# Push to ACR
az acr login --name upeuacr
docker push upeuacr.azurecr.io/upeu-ppp:latest

# Deploy to App Service
az webapp config container set \
  --name app-upeu-ppp \
  --resource-group rg-upeu-ppp \
  --docker-custom-image-name upeuacr.azurecr.io/upeu-ppp:latest
```

---

### **5. Celery en Azure**

#### **Opción A: Azure Container Instances (Recomendado)**

```bash
# Celery Worker
az container create \
  --resource-group rg-upeu-ppp \
  --name celery-worker \
  --image upeuacr.azurecr.io/upeu-ppp:latest \
  --cpu 1 \
  --memory 2 \
  --command-line "celery -A config worker --loglevel=info" \
  --environment-variables \
    DATABASE_URL="..." \
    REDIS_URL="..."

# Celery Beat
az container create \
  --resource-group rg-upeu-ppp \
  --name celery-beat \
  --image upeuacr.azurecr.io/upeu-ppp:latest \
  --cpu 1 \
  --memory 1 \
  --command-line "celery -A config beat --loglevel=info" \
  --environment-variables \
    DATABASE_URL="..." \
    REDIS_URL="..."
```

**Costo**: ~$15-30/mes por container

#### **Opción B: Azure Functions (Serverless)**

Convertir tareas Celery a Azure Functions (requiere refactorización)

---

### **6. Archivos necesarios para Azure**

#### **A) `startup.sh` (Startup command)**

Crear en raíz:

```bash
#!/bin/bash
# startup.sh - Azure App Service startup script

echo "🚀 Starting UPEU PPP System..."

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "🗄️  Running migrations..."
python manage.py migrate --noinput

# Create superuser if not exists (opcional)
echo "👤 Creating superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@upeu.edu.pe', 'AdminPassword123!')
EOF

# Start Gunicorn
echo "🌐 Starting Gunicorn..."
gunicorn --bind 0.0.0.0:8000 \
         --workers 4 \
         --timeout 120 \
         --access-logfile - \
         --error-logfile - \
         config.wsgi:application
```

Configurar en App Service:
```bash
az webapp config set \
  --name app-upeu-ppp \
  --resource-group rg-upeu-ppp \
  --startup-file "startup.sh"
```

#### **B) `azure-pipelines.yml` (Azure DevOps CI/CD)**

```yaml
trigger:
  - master

pool:
  vmImage: 'ubuntu-latest'

variables:
  pythonVersion: '3.11'

stages:
- stage: Build
  jobs:
  - job: BuildJob
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(pythonVersion)'
    
    - script: |
        pip install -r requirements/production.txt
        python manage.py test
      displayName: 'Install dependencies and run tests'
    
    - task: ArchiveFiles@2
      inputs:
        rootFolderOrFile: '$(Build.SourcesDirectory)'
        includeRootFolder: false
        archiveType: 'zip'
        archiveFile: '$(Build.ArtifactStagingDirectory)/$(Build.BuildId).zip'
    
    - task: PublishBuildArtifacts@1
      inputs:
        PathtoPublish: '$(Build.ArtifactStagingDirectory)'
        ArtifactName: 'drop'

- stage: Deploy
  dependsOn: Build
  jobs:
  - deployment: DeployWeb
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - task: AzureWebApp@1
            inputs:
              azureSubscription: 'Azure subscription'
              appName: 'app-upeu-ppp'
              package: '$(Pipeline.Workspace)/drop/$(Build.BuildId).zip'
```

---

### **7. Monitoreo y Logging en Azure**

#### **Application Insights**

```bash
# Crear Application Insights
az monitor app-insights component create \
  --app appinsights-upeu-ppp \
  --location eastus \
  --resource-group rg-upeu-ppp

# Conectar con App Service
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app appinsights-upeu-ppp \
  --resource-group rg-upeu-ppp \
  --query instrumentationKey -o tsv)

az webapp config appsettings set \
  --name app-upeu-ppp \
  --resource-group rg-upeu-ppp \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY="$INSTRUMENTATION_KEY"
```

**Agregar en `requirements/production.txt`**:
```
opencensus-ext-azure==1.1.9
opencensus-ext-django==0.8.0
```

**Configurar en `settings.py`**:
```python
MIDDLEWARE = [
    'opencensus.ext.django.middleware.OpencensusMiddleware',
    ...
]

OPENCENSUS = {
    'TRACE': {
        'SAMPLER': 'opencensus.trace.samplers.ProbabilitySampler(rate=1.0)',
        'EXPORTER': '''opencensus.ext.azure.trace_exporter.AzureExporter(
            connection_string="InstrumentationKey={}"
        )'''.format(os.getenv('APPINSIGHTS_INSTRUMENTATIONKEY')),
    }
}
```

---

### **8. Backup y Disaster Recovery**

```bash
# Backup automático de PostgreSQL ya configurado (30 días)

# Backup manual
az postgres flexible-server backup create \
  --resource-group rg-upeu-ppp \
  --server-name psql-upeu-ppp \
  --backup-name manual-backup-$(date +%Y%m%d)

# Restore desde backup
az postgres flexible-server restore \
  --resource-group rg-upeu-ppp \
  --name psql-upeu-ppp-restored \
  --source-server psql-upeu-ppp \
  --restore-time "2024-01-01T00:00:00Z"
```

---

### **9. Escalado Automático**

```bash
# Configurar autoscaling rules
az monitor autoscale create \
  --resource-group rg-upeu-ppp \
  --resource /subscriptions/{subscription-id}/resourceGroups/rg-upeu-ppp/providers/Microsoft.Web/serverfarms/plan-upeu-production \
  --name autoscale-upeu \
  --min-count 2 \
  --max-count 5 \
  --count 2

# Scale up por CPU
az monitor autoscale rule create \
  --resource-group rg-upeu-ppp \
  --autoscale-name autoscale-upeu \
  --condition "Percentage CPU > 70 avg 5m" \
  --scale out 1

# Scale down por CPU
az monitor autoscale rule create \
  --resource-group rg-upeu-ppp \
  --autoscale-name autoscale-upeu \
  --condition "Percentage CPU < 30 avg 10m" \
  --scale in 1
```

---

### **10. Costos Estimados Azure (Mensual)**

| Servicio | Tier | Costo |
|----------|------|-------|
| App Service Plan P1V3 | Premium | $100 |
| PostgreSQL Flexible Server | General Purpose | $110 |
| Redis Cache Standard C1 | Standard | $75 |
| Cosmos DB Serverless | Serverless | $25 |
| Blob Storage | Standard LRS | $5 |
| Application Insights | Standard | $10 |
| Container Instances (2) | Standard | $30 |
| Bandwidth | 100GB | $10 |
| **TOTAL ESTIMADO** | | **~$365/mes** |

💡 **Optimización de costos**:
- Usar **Azure for Students** ($100/mes gratis)
- **Reserved Instances** (ahorro 30-50%)
- **Dev/Test pricing** (descuento 20-40%)

---

## 📊 Comparación Final: ¿Cuál elegir?

### **Elige RENDER si:**
- ✅ Proyecto de graduación/académico
- ✅ Presupuesto limitado ($35-50/mes)
- ✅ Quieres desplegar rápido (1 hora)
- ✅ No necesitas alta disponibilidad crítica
- ✅ Audiencia pequeña (<1000 usuarios concurrentes)

### **Elige AZURE si:**
- ✅ Producción empresarial seria
- ✅ Presupuesto >$300/mes
- ✅ Necesitas SLA 99.95%+
- ✅ Compliance y seguridad crítica
- ✅ Escalabilidad masiva (>10,000 usuarios)
- ✅ Integración con sistemas corporativos

---

## 🚀 Recomendación Final

### **Para tu proyecto de graduación:**

**FASE 1 - Desarrollo/Demo (Render)**
- Usar **Render** para presentación y demo
- Costo: ~$35/mes
- Deploy en 1 hora
- Suficiente para mostrar funcionalidad

**FASE 2 - Producción (si la universidad lo adopta)**
- Migrar a **Azure** 
- Aprovechar **Azure for Students**
- Escalabilidad preparada
- Soporte empresarial

---

## 📚 Recursos Adicionales

### **Render**
- Docs: https://render.com/docs
- Community: https://community.render.com
- Status: https://status.render.com

### **Azure**
- Docs: https://docs.microsoft.com/azure
- Learning: https://learn.microsoft.com/training/azure
- Pricing Calculator: https://azure.microsoft.com/pricing/calculator
- Students: https://azure.microsoft.com/free/students

---

## ✅ Checklist Pre-Deployment

### **Para ambas plataformas:**
- [ ] Variables de entorno configuradas
- [ ] SECRET_KEY generado (64+ caracteres)
- [ ] DEBUG=False en producción
- [ ] ALLOWED_HOSTS configurado
- [ ] Base de datos migradas
- [ ] Static files configurados
- [ ] SSL/HTTPS habilitado
- [ ] Backups configurados
- [ ] Monitoreo configurado
- [ ] Tests pasando 100%
- [ ] Documentación actualizada

---

¿Necesitas ayuda con alguno de los dos despliegues? ¡Estoy aquí para asistirte! 🚀
