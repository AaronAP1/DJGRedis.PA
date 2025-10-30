# 🚀 DEPLOYMENT DE DJANGO A AZURE APP SERVICE

## 📋 **DESCRIPCIÓN**
Guía para desplegar la API REST del Sistema de Prácticas Profesionales UPeU en **Azure App Service** con el Free Tier **F1** (sin costo).

---

## 🎯 **CARACTERÍSTICAS DEL DEPLOYMENT**

### **Servicio: Azure App Service (Linux)**
- **SKU**: F1 (Free Tier) - $0/mes
- **Runtime**: Python 3.11
- **Deployment**: Azure CLI + `az webapp up`
- **Static Files**: WhiteNoise (sin Azure Storage)
- **Base de Datos**: PostgreSQL Flexible Server (ya desplegada)
- **Cache**: Redis Cache (ya desplegada)
- **Documents**: Cosmos DB MongoDB API (ya desplegada)

### **URLs Disponibles**
- **API Base**: `https://<webapp-name>.azurewebsites.net/api/`
- **Admin Panel**: `https://<webapp-name>.azurewebsites.net/admin/`
- **Swagger UI**: `https://<webapp-name>.azurewebsites.net/swagger/`
- **GraphQL**: `https://<webapp-name>.azurewebsites.net/graphql/`
- **Health Check**: `https://<webapp-name>.azurewebsites.net/health/`

---

## 📦 **PREREQUISITOS**

### 1. **Bases de Datos Desplegadas** (✅ Ya completado)
```bash
# Verificar recursos existentes
az resource list --resource-group rg-upeu-ppp-students --output table
```

**Recursos esperados:**
- ✅ PostgreSQL: `psql-upeu-ppp-5628`
- ✅ Redis: `redis-upeu-ppp-1147`
- ✅ Cosmos DB: `cosmos-upeu-ppp-2725`

### 2. **Archivo `.env.azure`** (✅ Ya existe)
Contiene las credenciales de conexión a las bases de datos Azure.

### 3. **Archivos de Deployment**
- ✅ `requirements.txt` - Dependencias de producción
- ✅ `config/settings.py` - Configuración actualizada con WhiteNoise
- ✅ `scripts/deploy_django_azure.ps1` - Script de deployment automatizado

---

## 🚀 **DEPLOYMENT PASO A PASO**

### **Opción 1: Deployment Automatizado (RECOMENDADO)**

```powershell
# Ejecutar script de deployment
cd C:\Users\xdxdxdxd\OneDrive - Universidad Peruana Unión\Escritorio\DJGRedis.PA
.\scripts\deploy_django_azure.ps1
```

**El script realiza:**
1. ✅ Verifica autenticación Azure
2. ✅ Crea App Service Plan (F1 - Free)
3. ✅ Crea Web App con runtime Python 3.11
4. ✅ Configura variables de entorno desde `.env.azure`
5. ✅ Configura startup command con Gunicorn
6. ✅ Despliega el código fuente
7. ✅ Ejecuta migraciones automáticamente

**Tiempo estimado**: 5-10 minutos

---

### **Opción 2: Deployment Manual**

#### **Paso 1: Crear App Service Plan**
```bash
az appservice plan create \
  --name asp-upeu-ppp \
  --resource-group rg-upeu-ppp-students \
  --location brazilsouth \
  --is-linux \
  --sku F1
```

#### **Paso 2: Crear Web App**
```bash
az webapp create \
  --name upeu-ppp-api-<RANDOM> \
  --resource-group rg-upeu-ppp-students \
  --plan asp-upeu-ppp \
  --runtime "PYTHON:3.11"
```

#### **Paso 3: Configurar Variables de Entorno**
```bash
# Leer desde .env.azure y configurar
az webapp config appsettings set \
  --name upeu-ppp-api-<RANDOM> \
  --resource-group rg-upeu-ppp-students \
  --settings @.env.azure
```

**Variables críticas:**
- `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (PostgreSQL Azure)
- `REDIS_URL` (Redis Azure)
- `MONGODB_URI` (Cosmos DB)
- `DEBUG=False`
- `ALLOWED_HOSTS=upeu-ppp-api-<RANDOM>.azurewebsites.net`
- `SECRET_KEY` (generar uno nuevo)

#### **Paso 4: Configurar Startup Command**
```bash
az webapp config set \
  --name upeu-ppp-api-<RANDOM> \
  --resource-group rg-upeu-ppp-students \
  --startup-file "gunicorn --bind=0.0.0.0 --timeout 600 config.wsgi"
```

#### **Paso 5: Desplegar Código**
```bash
az webapp up \
  --name upeu-ppp-api-<RANDOM> \
  --resource-group rg-upeu-ppp-students \
  --runtime "PYTHON:3.11" \
  --sku F1
```

---

## 🔧 **CONFIGURACIONES POST-DEPLOYMENT**

### **1. Crear Superusuario**
```bash
# Conectar a SSH de App Service
az webapp ssh --name upeu-ppp-api-<RANDOM> --resource-group rg-upeu-ppp-students

# Dentro del contenedor
python manage.py createsuperuser
```

### **2. Collect Static Files** (Automático con WhiteNoise)
WhiteNoise maneja archivos estáticos automáticamente durante el request. No requiere `collectstatic` manual.

### **3. Verificar Migraciones**
```bash
# Ejecutar migraciones manualmente si es necesario
az webapp ssh --name upeu-ppp-api-<RANDOM> --resource-group rg-upeu-ppp-students
python manage.py migrate
```

### **4. Configurar CORS** (Para Frontend)
Actualizar `.env.azure` con:
```env
CORS_ALLOWED_ORIGINS=https://frontend-domain.com,https://otro-dominio.com
CORS_ALLOW_CREDENTIALS=True
```

---

## 📊 **VERIFICACIÓN DEL DEPLOYMENT**

### **1. Health Check**
```bash
curl https://upeu-ppp-api-<RANDOM>.azurewebsites.net/health/
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "mongodb": "connected"
}
```

### **2. Test de Endpoints**

#### **Login (JWT)**
```bash
curl -X POST https://upeu-ppp-api-<RANDOM>.azurewebsites.net/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin123!"
  }'
```

#### **Swagger UI**
```
https://upeu-ppp-api-<RANDOM>.azurewebsites.net/swagger/
```

#### **GraphQL Playground**
```
https://upeu-ppp-api-<RANDOM>.azurewebsites.net/graphql/
```

### **3. Ver Logs en Tiempo Real**
```bash
az webapp log tail \
  --name upeu-ppp-api-<RANDOM> \
  --resource-group rg-upeu-ppp-students
```

### **4. Logs de Application Insights** (Opcional)
```bash
# Habilitar logging detallado
az webapp log config \
  --name upeu-ppp-api-<RANDOM> \
  --resource-group rg-upeu-ppp-students \
  --application-logging filesystem \
  --level information
```

---

## 🔐 **SEGURIDAD EN PRODUCCIÓN**

### **Variables de Entorno Críticas**
```env
# NUNCA usar valores por defecto en producción
SECRET_KEY=<GENERAR_NUEVO_KEY_LARGO>
DEBUG=False
ALLOWED_HOSTS=upeu-ppp-api-<RANDOM>.azurewebsites.net

# JWT Tokens
JWT_ACCESS_TOKEN_LIFETIME=15  # minutos
JWT_REFRESH_TOKEN_LIFETIME=5  # días
JWT_SECRET_KEY=<DIFERENTE_DE_SECRET_KEY>

# Rate Limiting (ya configurado en settings.py)
# - Login: 10/min
# - API: 1000/hour
# - GraphQL: 200/hour

# SSL/TLS (automático en Azure App Service)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### **Firewall de PostgreSQL**
El firewall ya está configurado para permitir servicios Azure:
```bash
# Verificar reglas
az postgres flexible-server firewall-rule list \
  --name psql-upeu-ppp-5628 \
  --resource-group rg-upeu-ppp-students
```

---

## 💰 **COSTOS**

| Servicio | SKU | Costo/Mes | Estado |
|----------|-----|-----------|--------|
| **App Service** | F1 (Free) | **$0** | ✅ Gratis |
| PostgreSQL | Standard_B1ms | $15 | ✅ Student Credit |
| Redis | Basic C0 | $16 | ✅ Student Credit |
| Cosmos DB | Serverless | $5-10 | ✅ Student Credit |
| **TOTAL** | | **$0** | **100% Cubierto** |

**Nota**: El App Service F1 tiene limitaciones:
- 60 minutos CPU/día
- 1 GB RAM
- 1 GB Storage
- No auto-scaling
- **Ideal para desarrollo y demos**

---

## 🔄 **CI/CD (Siguiente Fase)**

### **Opciones de CI/CD**
1. **GitHub Actions** (Recomendado)
2. **Azure DevOps**
3. **Azure Deployment Center**

**Workflow básico:**
```yaml
name: Deploy to Azure App Service

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Deploy to Azure
        uses: azure/webapps-deploy@v2
        with:
          app-name: upeu-ppp-api-<RANDOM>
          publish-profile: ${{ secrets.AZURE_PUBLISH_PROFILE }}
```

---

## 🐛 **TROUBLESHOOTING**

### **Error: "No module named 'config'"**
**Solución**: Verificar que `PYTHONPATH` incluya el directorio raíz:
```bash
az webapp config appsettings set \
  --name upeu-ppp-api-<RANDOM> \
  --resource-group rg-upeu-ppp-students \
  --settings PYTHONPATH=/home/site/wwwroot
```

### **Error: "Database connection refused"**
**Solución**: Verificar firewall de PostgreSQL permite Azure services:
```bash
az postgres flexible-server firewall-rule create \
  --resource-group rg-upeu-ppp-students \
  --name psql-upeu-ppp-5628 \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### **Error: "Static files not found"**
**Solución**: WhiteNoise está configurado, verificar middleware:
```python
# En config/settings.py debe estar:
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Después de SecurityMiddleware
    # ...
]
```

### **App muy lenta o timeout**
**Solución**: Free tier F1 tiene limitaciones. Opciones:
1. Escalar a **B1** ($13/mes) con Azure for Students
2. Optimizar queries (índices, select_related, prefetch_related)
3. Implementar caché Redis agresivo

---

## 📝 **COMANDOS ÚTILES**

```bash
# Ver estado de la App
az webapp show --name upeu-ppp-api-<RANDOM> -g rg-upeu-ppp-students

# Reiniciar App
az webapp restart --name upeu-ppp-api-<RANDOM> -g rg-upeu-ppp-students

# Escalar (cambiar SKU)
az appservice plan update --name asp-upeu-ppp -g rg-upeu-ppp-students --sku B1

# Ver logs de deployment
az webapp log deployment show --name upeu-ppp-api-<RANDOM> -g rg-upeu-ppp-students

# Ejecutar comando en contenedor
az webapp ssh --name upeu-ppp-api-<RANDOM> -g rg-upeu-ppp-students

# Descargar logs
az webapp log download --name upeu-ppp-api-<RANDOM> -g rg-upeu-ppp-students

# Eliminar App (si es necesario)
az webapp delete --name upeu-ppp-api-<RANDOM> -g rg-upeu-ppp-students
```

---

## 📧 **SIGUIENTE PASO: COMPARTIR CON FRONTEND**

Una vez desplegado, compartir con el equipo de frontend:

```
=======================================
 API DISPONIBLE EN LA NUBE ☁️
=======================================

Base URL: https://upeu-ppp-api-<RANDOM>.azurewebsites.net

ENDPOINTS PRINCIPALES:
- Swagger: /swagger/
- GraphQL: /graphql/
- Login: /api/v1/auth/login/
- Users: /api/v1/users/
- Empresas: /api/v1/empresas/
- Prácticas: /api/v1/practicas/

AUTENTICACIÓN:
- Tipo: JWT Bearer Token
- Header: Authorization: Bearer <token>
- Login con username (no email)

CORS: Configurado para dominios autorizados
Rate Limit: 1000 requests/hour por usuario

DOCUMENTACIÓN:
- Ver Swagger para detalles completos de cada endpoint
- GraphQL introspection habilitado
=======================================
```

---

## ✅ **CHECKLIST DE DEPLOYMENT**

- [ ] Bases de datos Azure desplegadas y accesibles
- [ ] `.env.azure` con todas las variables de entorno
- [ ] `requirements.txt` actualizado con gunicorn y whitenoise
- [ ] `settings.py` configurado para producción
- [ ] App Service creado con runtime Python 3.11
- [ ] Variables de entorno configuradas en App Service
- [ ] Código desplegado con `az webapp up`
- [ ] Migraciones ejecutadas correctamente
- [ ] Superusuario creado
- [ ] Health check responde correctamente
- [ ] Swagger UI accesible
- [ ] GraphQL Playground accesible
- [ ] API REST endpoints funcionando
- [ ] CORS configurado para frontend
- [ ] SSL/TLS activo (https)
- [ ] Logs monitoreados

---

**Fecha**: 30 de Octubre 2025  
**Proyecto**: Sistema de Prácticas Profesionales UPeU  
**Ambiente**: Azure App Service F1 (Free Tier)  
**Estado**: ✅ Listo para desplegar
