# ===========================================
# INSTRUCCIONES POST-LIMPIEZA DE SECRETOS
# ===========================================

## ✅ Problema Resuelto

El push a GitHub se realizó exitosamente después de:
1. Eliminar archivos con secretos (.env.azure, azure_credentials_*.txt)
2. Actualizar .gitignore para excluir archivos sensibles
3. Modificar scripts para usar variables de entorno
4. Crear commit limpio sin secretos hardcoded

## ⚠️ ACCIÓN REQUERIDA: Rotar Credenciales Comprometidas

Las siguientes credenciales fueron expuestas y DEBEN ser rotadas:

### 1. Azure Redis Cache Key
- **Recurso**: Redis Cache
- **Acción**: Regenerar las claves de acceso
```bash
az redis regenerate-keys --name <tu-redis-name> --resource-group <tu-resource-group> --key-type Primary
```

### 2. Azure Cosmos DB Key
- **Recurso**: Cosmos DB (cosmos-upeu-ppp-2725)
- **Acción**: Regenerar las claves primarias
```bash
az cosmosdb keys regenerate --name cosmos-upeu-ppp-2725 --resource-group rg-upeu-ppp-students --key-type primary
```

## 📝 Configurar Variables de Entorno Localmente

Crear archivo `.env.azure` (este archivo NO se subirá a GitHub):

```bash
# Copiar desde .env.example
cp .env.example .env.azure
```

Luego editar `.env.azure` con tus nuevas credenciales:

```env
# Azure Cosmos DB
AZURE_COSMOS_CONNECTION_STRING=mongodb://cosmos-upeu-ppp-2725:<NUEVA_KEY>@cosmos-upeu-ppp-2725.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@cosmos-upeu-ppp-2725@
AZURE_COSMOS_DATABASE=upeu_documents

# Azure Redis Cache
AZURE_REDIS_HOST=<tu-redis>.redis.cache.windows.net
AZURE_REDIS_PORT=6380
AZURE_REDIS_PASSWORD=<NUEVA_KEY>
AZURE_REDIS_SSL=True

# PostgreSQL
POSTGRES_PASSWORD=<tu-password>
MONGODB_PASSWORD=<tu-password>
```

## 🔐 Configurar Secretos en GitHub Actions

Para CI/CD, agregar secretos en GitHub:
1. Ve a: Repository Settings → Secrets and variables → Actions
2. Agrega los siguientes secretos:

- `AZURE_COSMOS_CONNECTION_STRING`
- `AZURE_REDIS_PASSWORD`
- `POSTGRES_PASSWORD`
- `MONGODB_PASSWORD`

## 📚 Archivos Seguros Ahora

✅ `.gitignore` actualizado para excluir:
- `.env*` (todos los archivos de entorno)
- `azure_credentials*.txt`
- `*_credentials*.txt`

✅ Scripts actualizados para usar `os.getenv()`:
- `scripts/migrate_mongo_to_azure.py`
- `scripts/test_cosmos_connection.py`

## 🚀 Próximos Pasos

1. **INMEDIATAMENTE**: Rotar las credenciales de Azure
2. Crear `.env.azure` local con las nuevas credenciales
3. Actualizar secretos en Azure App Service si los usas
4. Verificar que la aplicación funciona con las nuevas credenciales

## 📖 Documentación Relacionada

- `.env.example` - Plantilla de variables de entorno
- `docs/DEPLOYMENT_DJANGO_AZURE.md` - Guía de deployment
- `docs/GITHUB_ACTIONS_DEPLOYMENT.md` - Configuración de CI/CD
