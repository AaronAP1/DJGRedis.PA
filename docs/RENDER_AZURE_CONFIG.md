# 🔐 Guía de Configuración de Variables de Entorno en Render

## 📋 Índice
1. [¿Qué archivo usa Render?](#qué-archivo-usa-render)
2. [Configurar Variables Secretas](#configurar-variables-secretas)
3. [Obtener Credenciales de Azure](#obtener-credenciales-de-azure)
4. [Verificación](#verificación)

---

## ❌ ¿Qué archivo usa Render?

### Render NO usa archivos `.env`

Los siguientes archivos están en `.gitignore` y **NO se suben a Render**:
- `.env`
- `.env.local`
- `.env.production`
- `.env.azure`

### ✅ Render usa 2 fuentes:

#### 1️⃣ `render.azure.yaml` (Blueprint)
Define la estructura del servicio y valores **públicos/no sensibles**.

Variables marcadas con `sync: false` **deben configurarse manualmente** en el Dashboard de Render.

#### 2️⃣ Render Dashboard (Manual)
Variables secretas (passwords, keys) se configuran en:
```
Render Dashboard → Tu servicio → Environment → Add Environment Variable
```

---

## 🔑 Configurar Variables Secretas

### Paso 1: Acceder al Dashboard

1. Ve a [dashboard.render.com](https://dashboard.render.com)
2. Selecciona tu servicio `upeu-ppp-backend-azure`
3. Click en **"Environment"** en el menú lateral
4. Click en **"Add Environment Variable"**

### Paso 2: Azure PostgreSQL

Agregar las siguientes variables (marcar `DB_PASSWORD` como **Secret**):

```
Key: DB_HOST
Value: psql-upeu-ppp-5628.postgres.database.azure.com
```

```
Key: DB_USER
Value: <tu-usuario-azure>
```

```  
Key: DB_PASSWORD
Value: <tu-password-azure>
☑ Secret (marcar este checkbox)
```

```
Key: DATABASE_URL
Value: postgresql://<USER>:<PASSWORD>@<HOST>:5432/upeu_ppp?sslmode=require
```

> **Ejemplo**:
> ```
> postgresql://miusuario:mipassword@psql-upeu-ppp-5628.postgres.database.azure.com:5432/upeu_ppp?sslmode=require
> ```

### Paso 3: Azure Redis Cache (Opcional)

```
Key: REDIS_HOST
Value: redis-upeu-ppp-1147.redis.cache.windows.net
```

```
Key: REDIS_PASSWORD
Value: <tu-redis-key>
☑ Secret
```

```
Key: REDIS_URL
Value: rediss://:<PASSWORD>@<HOST>:6380/0?ssl_cert_reqs=required
```

> **Ejemplo**:
> ```
> rediss://:miRedisKey123@redis-upeu-ppp-1147.redis.cache.windows.net:6380/0?ssl_cert_reqs=required
> ```

### Paso 4: Azure Cosmos DB (Opcional)

```
Key: MONGODB_URI
Value: <connection-string-desde-azure>
☑ Secret
```

### Paso 5: Celery (Usa misma URL que Redis)

```
Key: CELERY_BROKER_URL
Value: <mismo-valor-que-REDIS_URL>
```

```
Key: CELERY_RESULT_BACKEND
Value: <mismo-valor-que-REDIS_URL>
```

---

## 🔍 Obtener Credenciales de Azure

### PostgreSQL

```powershell
# Ver detalles del servidor
az postgres flexible-server show `
  --name psql-upeu-ppp-5628 `
  --resource-group rg-upeu-ppp-students

# El usuario y password son los que configuraste al crear el servidor
```

### Redis Cache

```powershell
# Obtener las claves
az redis list-keys `
  --name redis-upeu-ppp-1147 `
  --resource-group rg-upeu-ppp-students `
  --query primaryKey `
  --output tsv
```

### Cosmos DB (MongoDB API)

```powershell
# Obtener connection string
az cosmosdb keys list `
  --name cosmos-upeu-ppp-2725 `
  --resource-group rg-upeu-ppp-students `
  --type connection-strings `
  --query "connectionStrings[0].connectionString" `
  --output tsv
```

---

## ✅ Verificación

### 1. Variables Configuradas

Verifica que en Render Dashboard → Environment tengas:

- ✅ `DATABASE_URL` (Secret)
- ✅ `DB_HOST`
- ✅ `DB_USER`
- ✅ `DB_PASSWORD` (Secret)
- ✅ `REDIS_URL` (Secret, opcional)
- ✅ `REDIS_HOST` (opcional)
- ✅ `REDIS_PASSWORD` (Secret, opcional)
- ✅ `MONGODB_URI` (Secret, opcional)
- ✅ `CELERY_BROKER_URL` (opcional)
- ✅ `CELERY_RESULT_BACKEND` (opcional)

### 2. Re-deploy

Después de configurar las variables:
1. Click en **"Manual Deploy"** → **"Deploy latest commit"**
2. Esperar a que complete el build
3. Verificar logs para confirmar conexión a bases de datos

### 3. Verificar Conexiones

En los logs de Render deberías ver:
```
Connecting to PostgreSQL: psql-upeu-ppp-5628.postgres.database.azure.com
✓ Database connection successful
✓ Redis connection successful (si está configurado)
```

---

## 🚨 Importante

### Seguridad

1. **NUNCA** subir archivos con credenciales al repositorio
2. **SIEMPRE** marcar passwords y keys como **Secret** en Render
3. **Rotar** credenciales si fueron expuestas accidentalmente

### .gitignore

Verifica que estos archivos estén en `.gitignore`:

```gitignore
# Environment variables
.env
.env.*
azure_credentials*.txt
*_credentials*.txt

# ZIP files
*.zip
```

### Problemas Comunes

**Error: "Connection refused"**
- Verifica que el servidor de Azure permita conexiones desde Render
- Agrega las IPs de Render a las reglas de firewall de Azure

**Error: "Authentication failed"**
- Verifica usuario y password en Render Dashboard
- Asegúrate de usar el formato correcto en `DATABASE_URL`

**Timeout en conexión**
- Verifica que `sslmode=require` esté en `DATABASE_URL`
- Para Cosmos DB, verifica que `ssl=true` esté en `MONGODB_URI`

---

## 📚 Recursos

- [Render Environment Variables](https://render.com/docs/environment-variables)
- [Azure PostgreSQL Connection Strings](https://docs.microsoft.com/en-us/azure/postgresql/)
- [Azure Redis Cache](https://docs.microsoft.com/en-us/azure/azure-cache-for-redis/)
- [Azure Cosmos DB MongoDB API](https://docs.microsoft.com/en-us/azure/cosmos-db/mongodb/)
