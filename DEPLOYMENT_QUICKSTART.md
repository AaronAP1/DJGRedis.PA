# 🚀 Guía Rápida de Despliegue

Este documento te guía paso a paso para desplegar el sistema en **Render** o **Azure**.

---

## 📚 Documentación Completa

Para detalles completos, consulta: [`docs/DEPLOYMENT_RENDER_VS_AZURE.md`](docs/DEPLOYMENT_RENDER_VS_AZURE.md)

---

## ⚡ Opción 1: RENDER (Rápido y Económico)

**Ideal para**: Proyectos académicos, demos, startups  
**Costo**: ~$35/mes  
**Tiempo**: 30 minutos  

### Paso 1: Preparar MongoDB Atlas (Gratis)

```bash
# 1. Ve a https://www.mongodb.com/cloud/atlas
# 2. Crea cuenta y cluster M0 (FREE)
# 3. Crea database: upeu_documents
# 4. Obtén connection string:
mongodb+srv://upeu_admin:<password>@cluster0.xxxxx.mongodb.net/upeu_documents
```

### Paso 2: Conectar GitHub a Render

```bash
# 1. Ve a https://render.com
# 2. Regístrate con GitHub
# 3. Dashboard -> New -> Blueprint
# 4. Conecta repositorio: AaronAP1/DJGRedis.PA
# 5. Render detecta render.yaml automáticamente
```

### Paso 3: Configurar Variables

En Render Dashboard, agrega estas variables a **TODOS los servicios**:

```bash
# MongoDB (de Atlas)
MONGODB_URI=mongodb+srv://upeu_admin:<password>@cluster.mongodb.net/upeu_documents
MONGODB_DB_NAME=upeu_documents

# Email (Gmail ejemplo)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password

# CORS (si tienes frontend separado)
CORS_ALLOWED_ORIGINS=https://tu-frontend.com
```

### Paso 4: Deploy

```bash
# Click "Apply" en Render
# Render construye y despliega automáticamente
# Monitorea logs en tiempo real
```

### Paso 5: Verificar

```bash
# Health check
curl https://upeu-ppp-backend.onrender.com/api/health/

# Admin
https://upeu-ppp-backend.onrender.com/admin/

# Swagger
https://upeu-ppp-backend.onrender.com/api/swagger/
```

**✅ ¡Listo!** Tu app está en producción en ~30 minutos.

---

## ☁️ Opción 2: AZURE (Empresarial)

**Ideal para**: Producción crítica, empresas  
**Costo**: ~$315-365/mes  
**Tiempo**: 2-4 horas  

### Opción A: Deployment Automático (Recomendado)

```bash
# 1. Instala Azure CLI
# Windows: https://aka.ms/installazurecliwindows
# Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# 2. Login
az login

# 3. Ejecuta script automático
bash scripts/deploy_azure.sh

# 4. Sigue las instrucciones y guarda las credenciales
```

### Opción B: Deployment Manual

#### Paso 1: Crear Recursos Base

```bash
# Login
az login

# Variables
RESOURCE_GROUP="rg-upeu-ppp"
LOCATION="eastus"
WEBAPP_NAME="app-upeu-ppp"

# Resource Group
az group create --name $RESOURCE_GROUP --location $LOCATION

# App Service Plan
az appservice plan create \
  --name plan-upeu-production \
  --resource-group $RESOURCE_GROUP \
  --sku P1V3 \
  --is-linux

# Web App
az webapp create \
  --name $WEBAPP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan plan-upeu-production \
  --runtime "PYTHON:3.11"
```

#### Paso 2: Crear Bases de Datos

```bash
# PostgreSQL
az postgres flexible-server create \
  --name psql-upeu-ppp \
  --resource-group $RESOURCE_GROUP \
  --admin-user upeu_admin \
  --admin-password 'TuPassword123!' \
  --sku-name Standard_D2s_v3 \
  --version 15

# Redis
az redis create \
  --name redis-upeu-ppp \
  --resource-group $RESOURCE_GROUP \
  --sku Standard \
  --vm-size C1

# Cosmos DB (MongoDB)
az cosmosdb create \
  --name cosmos-upeu-ppp \
  --resource-group $RESOURCE_GROUP \
  --kind MongoDB
```

#### Paso 3: Configurar App Settings

```bash
az webapp config appsettings set \
  --name $WEBAPP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    DJANGO_SETTINGS_MODULE="config.settings" \
    DEBUG="False" \
    SECRET_KEY="<genera-uno-seguro>" \
    DATABASE_URL="postgres://..." \
    REDIS_URL="rediss://..." \
    MONGODB_URI="mongodb://..."
```

#### Paso 4: Deploy

```bash
# Crear ZIP
git archive -o app.zip HEAD

# Deploy
az webapp deployment source config-zip \
  --name $WEBAPP_NAME \
  --resource-group $RESOURCE_GROUP \
  --src app.zip
```

### Opción C: GitHub Actions (CI/CD)

```bash
# 1. El archivo .github/workflows/azure-deploy.yml ya está configurado

# 2. Crear Service Principal
az ad sp create-for-rbac \
  --name "github-actions-upeu" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/rg-upeu-ppp \
  --sdk-auth

# 3. Copiar JSON output

# 4. GitHub: Settings -> Secrets -> New secret
# Name: AZURE_CREDENTIALS
# Value: <pega el JSON>

# 5. Push a master para auto-deploy
git push origin master
```

---

## 🔧 Post-Deployment

### Crear Superusuario

```bash
# Render
render shell upeu-ppp-backend
python manage.py createsuperuser

# Azure
az webapp ssh --name app-upeu-ppp --resource-group rg-upeu-ppp
python manage.py createsuperuser
```

### Cargar Datos Iniciales

```bash
# Ejecutar migraciones SQL
python manage.py dbshell < docs/arquitectura/crear_bd_completa.sql

# O cargar fixtures
python manage.py loaddata initial_data.json
```

### Verificar Sistema

```bash
# Health check
curl https://tu-app.com/api/health/

# Check deployment
python manage.py check --deploy

# Test endpoints
curl https://tu-app.com/api/swagger/
curl https://tu-app.com/graphql/
```

---

## 🐛 Troubleshooting

### Render: App no inicia

```bash
# Ver logs
Render Dashboard -> Service -> Logs

# Verificar variables de entorno
Dashboard -> Service -> Environment

# Rebuild
Dashboard -> Service -> Manual Deploy -> Deploy latest commit
```

### Azure: Error 500

```bash
# Ver logs
az webapp log tail --name app-upeu-ppp --resource-group rg-upeu-ppp

# O en Portal
Azure Portal -> App Service -> Log stream

# Verificar startup
az webapp config show --name app-upeu-ppp --resource-group rg-upeu-ppp
```

### Base de datos no conecta

```bash
# Verificar connection string
echo $DATABASE_URL

# Test conexión
python manage.py dbshell

# Verificar firewall (Azure)
az postgres flexible-server firewall-rule list \
  --name psql-upeu-ppp \
  --resource-group rg-upeu-ppp
```

### Static files no cargan

```bash
# Render (usa WhiteNoise automáticamente)
python manage.py collectstatic --noinput

# Azure (configurar Azure Blob)
# Ver docs/DEPLOYMENT_RENDER_VS_AZURE.md sección Blob Storage
```

---

## 📊 Monitoreo

### Render

```bash
# Métricas básicas en Dashboard
Render Dashboard -> Service -> Metrics

# Logs en tiempo real
Dashboard -> Service -> Logs -> Live tail
```

### Azure

```bash
# Application Insights (si configurado)
Azure Portal -> Application Insights -> Live Metrics

# Logs
az monitor app-insights metrics show \
  --app appinsights-upeu-ppp \
  --resource-group rg-upeu-ppp \
  --metric requests/count

# Alertas
Portal -> Monitor -> Alerts -> New alert rule
```

---

## 💰 Costos Estimados

### Render
- **Free tier**: $0 (limitado)
- **Starter**: ~$35/mes
- **Standard**: ~$85/mes

### Azure
- **Desarrollo**: ~$150/mes (usando Azure for Students)
- **Producción**: ~$315/mes
- **Enterprise**: ~$500+/mes

---

## 📚 Recursos Adicionales

- [Documentación completa](docs/DEPLOYMENT_RENDER_VS_AZURE.md)
- [Guía de desarrollo](docs/GUIA_DESARROLLO.md)
- [Guía de testing](docs/GUIA_TESTING.md)
- [Arquitectura del sistema](docs/arquitectura/README.md)

---

## 🆘 Soporte

¿Necesitas ayuda?

1. Revisa logs del servicio
2. Consulta [Troubleshooting](#-troubleshooting)
3. Verifica variables de entorno
4. Revisa documentación completa

---

**¡Éxito con tu deployment!** 🚀
