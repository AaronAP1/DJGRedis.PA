# ☁️ Arquitectura de Despliegue en Azure - Sistema PPP UPeU

## 📊 Análisis Completo de Infraestructura Cloud

### 🎯 Objetivo
Desplegar el **Sistema de Gestión de Prácticas Profesionales** en Microsoft Azure con alta disponibilidad, escalabilidad y seguridad empresarial.

---

## 🏗️ Arquitectura Propuesta en Azure

### **Diagrama de Alto Nivel**

```
                          ┌──────────────────────────────────────────┐
                          │    Azure Front Door (CDN + WAF)         │
                          │  - SSL/TLS termination                  │
                          │  - DDoS protection                      │
                          │  - Global load balancing                │
                          └──────────────┬───────────────────────────┘
                                         │
                          ┌──────────────▼───────────────────────────┐
                          │    Azure Application Gateway            │
                          │  - Layer 7 load balancer                │
                          │  - URL-based routing                    │
                          │  - Web Application Firewall (WAF)       │
                          └──────────────┬───────────────────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              │                          │                          │
    ┌─────────▼─────────┐    ┌──────────▼──────────┐    ┌─────────▼─────────┐
    │  App Service (1)  │    │  App Service (2)    │    │  App Service (N)  │
    │  Django + Gunicorn│    │  Django + Gunicorn  │    │  Django + Gunicorn│
    │  - API REST       │    │  - API REST         │    │  - API REST       │
    │  - GraphQL        │    │  - GraphQL          │    │  - GraphQL        │
    │  - Static Files   │    │  - Static Files     │    │  - Static Files   │
    └─────────┬─────────┘    └──────────┬──────────┘    └─────────┬─────────┘
              │                          │                          │
              └──────────────────────────┼──────────────────────────┘
                                         │
                ┌────────────────────────┼────────────────────────┐
                │                        │                        │
     ┌──────────▼──────────┐  ┌─────────▼─────────┐  ┌──────────▼──────────┐
     │ Azure Database for  │  │ Azure Cache for   │  │ Azure Cosmos DB     │
     │ PostgreSQL          │  │ Redis             │  │ (MongoDB API)       │
     │ - Flexible Server   │  │ - Premium tier    │  │ - Document storage  │
     │ - Geo-replication   │  │ - Persistence     │  │ - Global distribution│
     │ - Automated backups │  │ - SSL/TLS         │  │ - Auto-scaling      │
     └─────────────────────┘  └───────────────────┘  └─────────────────────┘
                │                        │                        │
     ┌──────────▼──────────┐  ┌─────────▼─────────┐  ┌──────────▼──────────┐
     │ Azure Blob Storage  │  │ Azure Monitor     │  │ Azure Key Vault     │
     │ - Media files       │  │ - Application     │  │ - Secrets           │
     │ - Backups           │  │   Insights        │  │ - Certificates      │
     │ - Static files      │  │ - Logs            │  │ - Connection strings│
     └─────────────────────┘  └───────────────────┘  └─────────────────────┘
                                         │
                          ┌──────────────▼───────────────┐
                          │  Azure DevOps / GitHub       │
                          │  - CI/CD Pipelines           │
                          │  - Automated deployment      │
                          │  - Testing automation        │
                          └──────────────────────────────┘
```

---

## 🔧 Servicios de Azure Necesarios

### **1. Capa de Aplicación**

#### **App Service Plan (Premium)**
- **Servicio**: Azure App Service
- **SKU Recomendado**: P2V3 (Premium V3)
  - 2 vCores
  - 8 GB RAM
  - 250 GB almacenamiento
- **Características**:
  - ✅ Auto-scaling (2-5 instancias)
  - ✅ Custom domains + SSL
  - ✅ Deployment slots (staging/production)
  - ✅ Always On enabled
  - ✅ Linux container support

**Configuración**:
```bash
# Runtime stack: Python 3.11
# Framework: Django 5.0
# Web server: Gunicorn
```

**Costo estimado**: ~$150-200/mes por instancia

---

### **2. Bases de Datos**

#### **A) Azure Database for PostgreSQL (Flexible Server)**
- **Servicio**: Azure Database for PostgreSQL
- **SKU Recomendado**: General Purpose
  - 4 vCores
  - 16 GB RAM
  - 128 GB almacenamiento SSD
- **Características**:
  - ✅ Automated backups (7-35 días)
  - ✅ Point-in-time restore
  - ✅ Geo-redundant backups
  - ✅ Read replicas (opcional)
  - ✅ SSL/TLS enforcement
  - ✅ Private endpoint (VNet integration)

**Configuración**:
```sql
-- PostgreSQL 15
-- Database: upeu_ppp_system
-- Character set: UTF8
-- Locale: es_PE.UTF-8
```

**Costo estimado**: ~$200-250/mes

#### **B) Azure Cache for Redis (Premium)**
- **Servicio**: Azure Cache for Redis
- **SKU Recomendado**: Premium P1
  - 6 GB memoria
  - 20,000 conexiones
  - Replicación incluida
- **Características**:
  - ✅ Data persistence (RDB + AOF)
  - ✅ Clustering (opcional)
  - ✅ Geo-replication
  - ✅ SSL/TLS
  - ✅ Private endpoint

**Uso en el sistema**:
- Cache de sesiones Django
- Cache de consultas
- Rate limiting
- Celery broker (tareas asíncronas)

**Costo estimado**: ~$180-220/mes

#### **C) Azure Cosmos DB (MongoDB API)**
- **Servicio**: Azure Cosmos DB
- **SKU Recomendado**: Provisioned throughput
  - 400 RU/s (Request Units)
  - Auto-scaling enabled
- **Características**:
  - ✅ Global distribution (multi-region)
  - ✅ 99.99% SLA
  - ✅ Automatic indexing
  - ✅ Multi-model support
  - ✅ Point-in-time restore

**Uso en el sistema**:
- Almacenamiento de logs
- Documentos no estructurados
- Auditoría de acciones

**Costo estimado**: ~$25-50/mes (depende del throughput)

---

### **3. Almacenamiento**

#### **Azure Blob Storage (Hot Tier)**
- **Servicio**: Azure Storage Account
- **Tipo**: Standard (LRS o GRS)
- **Características**:
  - ✅ Almacenamiento ilimitado
  - ✅ CDN integration
  - ✅ Lifecycle policies
  - ✅ Soft delete
  - ✅ Versioning

**Contenedores**:
1. **`media`** - Archivos subidos por usuarios (PDFs, imágenes)
2. **`static`** - CSS, JS, assets estáticos
3. **`backups`** - Backups automáticos de BD

**Costo estimado**: ~$20-40/mes (primeros 50GB)

---

### **4. Seguridad**

#### **A) Azure Key Vault**
- **Servicio**: Azure Key Vault (Standard)
- **Uso**:
  - Secretos (DB passwords, API keys)
  - Certificados SSL
  - JWT secret keys
  - Cloudflare tokens

**Costo estimado**: ~$5/mes

#### **B) Azure Front Door (WAF + CDN)**
- **Servicio**: Azure Front Door
- **SKU**: Premium
- **Características**:
  - ✅ Global load balancing
  - ✅ Web Application Firewall (WAF)
  - ✅ DDoS protection (Layer 7)
  - ✅ SSL/TLS offloading
  - ✅ URL rewriting
  - ✅ Geo-filtering

**Costo estimado**: ~$100-150/mes

#### **C) Azure Application Gateway (WAF)**
- **Servicio**: Application Gateway v2
- **SKU**: WAF_v2
- **Características**:
  - ✅ Layer 7 load balancing
  - ✅ URL-based routing
  - ✅ SSL termination
  - ✅ Autoscaling

**Costo estimado**: ~$200-250/mes

---

### **5. Networking**

#### **Azure Virtual Network (VNet)**
- **Subnets**:
  1. **App Subnet** - App Services
  2. **Database Subnet** - PostgreSQL, Redis
  3. **Gateway Subnet** - Application Gateway
  
- **Características**:
  - ✅ Network Security Groups (NSG)
  - ✅ Private endpoints
  - ✅ Service endpoints
  - ✅ VNet peering (si multi-región)

**Costo**: Incluido

#### **Azure Private Link**
- **Uso**: Conexiones privadas a servicios PaaS
  - PostgreSQL
  - Redis
  - Cosmos DB
  - Storage Account

**Costo estimado**: ~$10-15/mes

---

### **6. Monitoring y Logs**

#### **A) Azure Monitor + Application Insights**
- **Características**:
  - ✅ APM (Application Performance Monitoring)
  - ✅ Distributed tracing
  - ✅ Custom metrics
  - ✅ Alertas automáticas
  - ✅ Live metrics

**Métricas monitoreadas**:
- Request rate (req/s)
- Response time (ms)
- Error rate (%)
- Database queries
- Cache hit ratio
- CPU/Memory usage

**Costo estimado**: ~$50-100/mes

#### **B) Azure Log Analytics**
- **Uso**:
  - Logs centralizados
  - Query language (KQL)
  - Retention policies
  - Custom dashboards

**Costo estimado**: ~$30-50/mes

---

### **7. CI/CD**

#### **Azure DevOps / GitHub Actions**
- **Pipelines**:
  1. **Build Pipeline**
     - Run tests (pytest)
     - Linting (flake8, black)
     - Security scan (bandit)
     - Build Docker image
  
  2. **Deployment Pipeline**
     - Deploy to staging slot
     - Run integration tests
     - Swap to production
     - Rollback on failure

**Costo**: Gratuito (GitHub Actions) o incluido (Azure DevOps)

---

### **8. Backup y Disaster Recovery**

#### **Azure Backup**
- **Estrategia 3-2-1**:
  - 3 copias de datos
  - 2 tipos de medios
  - 1 copia offsite

**Backups configurados**:
1. **PostgreSQL**: Automated backups (35 días)
2. **Redis**: RDB snapshots cada 6h
3. **Blob Storage**: Soft delete + versioning
4. **Cosmos DB**: Continuous backup

**Recovery Point Objective (RPO)**: 1 hora  
**Recovery Time Objective (RTO)**: 2 horas

**Costo estimado**: ~$30-50/mes

---

### **9. Email Service**

#### **Azure Communication Services**
o **SendGrid (Azure Marketplace)**

- **Uso**:
  - Notificaciones de sistema
  - Password reset
  - Confirmaciones de práctica
  - Reportes automáticos

**Costo estimado**: ~$10-20/mes (primeros 25,000 emails gratis con SendGrid)

---

## 💰 Resumen de Costos Mensuales

| Servicio | SKU/Tier | Costo Estimado (USD) |
|----------|----------|---------------------|
| **App Service Plan** | P2V3 (2 instancias) | $300-400 |
| **Azure Database for PostgreSQL** | General Purpose 4vCore | $200-250 |
| **Azure Cache for Redis** | Premium P1 | $180-220 |
| **Azure Cosmos DB** | 400 RU/s | $25-50 |
| **Blob Storage** | Hot tier | $20-40 |
| **Azure Front Door** | Premium + WAF | $100-150 |
| **Application Gateway** | WAF_v2 | $200-250 |
| **Key Vault** | Standard | $5 |
| **Private Link** | Standard | $10-15 |
| **Application Insights** | Standard | $50-100 |
| **Log Analytics** | Standard | $30-50 |
| **Backup** | Standard | $30-50 |
| **Email (SendGrid)** | Standard | $10-20 |
| **Bandwidth** | Salida de datos | $20-50 |

### **💵 TOTAL ESTIMADO: $1,180 - $1,595 USD/mes**

**Optimizaciones para reducir costos**:
- Usar Basic App Service en staging
- Redis Standard en lugar de Premium
- Front Door Standard en lugar de Premium
- Reserved instances (descuento 30-70%)

**Costo optimizado**: **$600-800 USD/mes**

---

## 🔐 Configuración de Seguridad

### **1. Identity and Access Management**

#### **Azure Active Directory (Entra ID)**
```yaml
Authentication:
  - User authentication: JWT + Azure AD B2C (opcional)
  - Service authentication: Managed Identity
  - API authentication: OAuth 2.0 + JWT

Authorization:
  - Role-Based Access Control (RBAC)
  - Roles: 
    - PRACTICANTE
    - SUPERVISOR
    - COORDINADOR
    - SECRETARIA
    - ADMINISTRADOR
```

### **2. Network Security**

```yaml
Firewall Rules:
  PostgreSQL:
    - Allow: App Service subnet (10.0.1.0/24)
    - Deny: All other traffic
    
  Redis:
    - Allow: App Service subnet (10.0.1.0/24)
    - Deny: All other traffic
    
  Cosmos DB:
    - Allow: App Service subnet (10.0.1.0/24)
    - Deny: All other traffic
    
  Blob Storage:
    - Allow: App Service + CDN
    - Deny: Direct public access

Application Gateway:
  - WAF Rules: OWASP Top 10
  - DDoS Protection: Standard
  - SSL/TLS: TLS 1.2+ only
  - Custom rules: Rate limiting, IP filtering
```

### **3. Data Encryption**

```yaml
At Rest:
  - PostgreSQL: Transparent Data Encryption (TDE)
  - Redis: Azure Disk Encryption
  - Cosmos DB: Encryption by default
  - Blob Storage: SSE-S (Server-Side Encryption)

In Transit:
  - HTTPS only (enforce SSL/TLS 1.2+)
  - Database connections: SSL required
  - Redis: TLS enabled
  - Internal traffic: Private Link
```

### **4. Secrets Management**

```yaml
Azure Key Vault:
  Secrets:
    - DB_PASSWORD
    - REDIS_PASSWORD
    - JWT_SECRET_KEY
    - CLOUDFLARE_SECRET_KEY
    - EMAIL_API_KEY
    - SECRET_KEY (Django)
  
  Access:
    - App Service: Managed Identity
    - DevOps Pipeline: Service Principal
    - Rotation: Automatic (90 días)
```

---

## 🚀 Estrategia de Despliegue

### **Fase 1: Infraestructura Base (Semana 1-2)**

```bash
# 1. Crear Resource Group
az group create \
  --name rg-upeu-ppp-prod \
  --location eastus2

# 2. Crear Virtual Network
az network vnet create \
  --resource-group rg-upeu-ppp-prod \
  --name vnet-upeu-ppp \
  --address-prefix 10.0.0.0/16 \
  --subnet-name snet-app \
  --subnet-prefix 10.0.1.0/24

# 3. Crear PostgreSQL
az postgres flexible-server create \
  --resource-group rg-upeu-ppp-prod \
  --name psql-upeu-ppp-prod \
  --location eastus2 \
  --admin-user upeu_admin \
  --admin-password <SECURE_PASSWORD> \
  --sku-name Standard_D4s_v3 \
  --tier GeneralPurpose \
  --storage-size 128 \
  --version 15 \
  --high-availability Enabled

# 4. Crear Redis
az redis create \
  --resource-group rg-upeu-ppp-prod \
  --name redis-upeu-ppp-prod \
  --location eastus2 \
  --sku Premium \
  --vm-size P1

# 5. Crear Cosmos DB (MongoDB API)
az cosmosdb create \
  --resource-group rg-upeu-ppp-prod \
  --name cosmos-upeu-ppp-prod \
  --kind MongoDB \
  --server-version 4.2 \
  --default-consistency-level Session

# 6. Crear Storage Account
az storage account create \
  --resource-group rg-upeu-ppp-prod \
  --name stupeupp prod \
  --location eastus2 \
  --sku Standard_GRS \
  --kind StorageV2 \
  --access-tier Hot

# 7. Crear Key Vault
az keyvault create \
  --resource-group rg-upeu-ppp-prod \
  --name kv-upeu-ppp-prod \
  --location eastus2 \
  --enabled-for-deployment true \
  --enabled-for-template-deployment true
```

### **Fase 2: Aplicación (Semana 3)**

```bash
# 1. Crear App Service Plan
az appservice plan create \
  --resource-group rg-upeu-ppp-prod \
  --name asp-upeu-ppp-prod \
  --location eastus2 \
  --is-linux \
  --sku P2V3 \
  --number-of-workers 2

# 2. Crear Web App
az webapp create \
  --resource-group rg-upeu-ppp-prod \
  --plan asp-upeu-ppp-prod \
  --name app-upeu-ppp-prod \
  --runtime "PYTHON:3.11"

# 3. Configurar deployment slots
az webapp deployment slot create \
  --resource-group rg-upeu-ppp-prod \
  --name app-upeu-ppp-prod \
  --slot staging

# 4. Configurar App Settings
az webapp config appsettings set \
  --resource-group rg-upeu-ppp-prod \
  --name app-upeu-ppp-prod \
  --settings \
    DEBUG=False \
    SECRET_KEY="@Microsoft.KeyVault(SecretUri=https://kv-upeu-ppp-prod.vault.azure.net/secrets/SECRET-KEY/)" \
    DB_HOST="psql-upeu-ppp-prod.postgres.database.azure.com" \
    DB_NAME="upeu_ppp_system" \
    DB_USER="upeu_admin" \
    DB_PASSWORD="@Microsoft.KeyVault(SecretUri=https://kv-upeu-ppp-prod.vault.azure.net/secrets/DB-PASSWORD/)" \
    REDIS_URL="rediss://redis-upeu-ppp-prod.redis.cache.windows.net:6380" \
    USE_REDIS_CACHE=True \
    ALLOWED_HOSTS="app-upeu-ppp-prod.azurewebsites.net,upeu-practicas.edu.pe"
```

### **Fase 3: Networking y Seguridad (Semana 4)**

```bash
# 1. Crear Application Gateway
az network application-gateway create \
  --resource-group rg-upeu-ppp-prod \
  --name agw-upeu-ppp-prod \
  --location eastus2 \
  --sku WAF_v2 \
  --capacity 2 \
  --vnet-name vnet-upeu-ppp \
  --subnet snet-gateway

# 2. Configurar Front Door
az afd profile create \
  --resource-group rg-upeu-ppp-prod \
  --profile-name afd-upeu-ppp-prod \
  --sku Premium_AzureFrontDoor

# 3. Configurar WAF Policy
az network front-door waf-policy create \
  --resource-group rg-upeu-ppp-prod \
  --name waf-upeu-ppp-prod \
  --sku Premium_AzureFrontDoor \
  --mode Prevention
```

### **Fase 4: Monitoring (Semana 5)**

```bash
# 1. Crear Application Insights
az monitor app-insights component create \
  --resource-group rg-upeu-ppp-prod \
  --app insights-upeu-ppp-prod \
  --location eastus2 \
  --application-type web

# 2. Crear Log Analytics Workspace
az monitor log-analytics workspace create \
  --resource-group rg-upeu-ppp-prod \
  --workspace-name la-upeu-ppp-prod \
  --location eastus2

# 3. Configurar alertas
az monitor metrics alert create \
  --resource-group rg-upeu-ppp-prod \
  --name "High CPU Alert" \
  --scopes "/subscriptions/<SUB_ID>/resourceGroups/rg-upeu-ppp-prod/providers/Microsoft.Web/sites/app-upeu-ppp-prod" \
  --condition "avg Percentage CPU > 80" \
  --window-size 5m \
  --evaluation-frequency 1m
```

---

## 📋 Checklist de Migración

### **Pre-Despliegue**
- [ ] Auditar código (security scan con bandit)
- [ ] Ejecutar todos los tests (>80% coverage)
- [ ] Generar requirements.txt de producción
- [ ] Crear Dockerfile optimizado
- [ ] Documentar variables de entorno
- [ ] Preparar scripts de migración de BD
- [ ] Backup de BD actual (local)

### **Infraestructura**
- [ ] Crear Resource Group
- [ ] Provisionar PostgreSQL
- [ ] Provisionar Redis
- [ ] Provisionar Cosmos DB
- [ ] Crear Storage Account
- [ ] Configurar Key Vault
- [ ] Crear Virtual Network
- [ ] Configurar Private Links

### **Aplicación**
- [ ] Crear App Service Plan
- [ ] Crear Web App
- [ ] Configurar deployment slots
- [ ] Migrar archivos estáticos a Blob Storage
- [ ] Configurar CDN para static files
- [ ] Configurar Application Settings
- [ ] Habilitar Managed Identity
- [ ] Conectar a Key Vault

### **Base de Datos**
- [ ] Migrar schema a Azure PostgreSQL
- [ ] Importar datos existentes
- [ ] Configurar backups automáticos
- [ ] Crear read replica (opcional)
- [ ] Optimizar índices
- [ ] Configurar connection pooling

### **Seguridad**
- [ ] Configurar WAF en Application Gateway
- [ ] Configurar Front Door
- [ ] Implementar SSL/TLS personalizado
- [ ] Configurar NSG rules
- [ ] Habilitar DDoS Protection
- [ ] Configurar IP whitelisting
- [ ] Rotar secrets en Key Vault

### **Monitoring**
- [ ] Configurar Application Insights
- [ ] Crear dashboards en Azure Monitor
- [ ] Configurar alertas (CPU, memoria, errores)
- [ ] Integrar logs con Log Analytics
- [ ] Configurar availability tests
- [ ] Configurar performance tests

### **CI/CD**
- [ ] Crear pipeline de build
- [ ] Crear pipeline de deployment
- [ ] Configurar automated tests
- [ ] Configurar deployment gates
- [ ] Probar rollback automático
- [ ] Documentar proceso de deployment

### **Post-Despliegue**
- [ ] Smoke tests en producción
- [ ] Load testing (Apache JMeter)
- [ ] Security penetration testing
- [ ] Validar backups automáticos
- [ ] Configurar disaster recovery
- [ ] Entrenar equipo en Azure Portal
- [ ] Documentar runbooks

---

## 🎯 Arquitectura por Ambientes

### **Development**
```yaml
App Service: B1 Basic (1 instancia)
PostgreSQL: B_Gen5_1 (1 vCore)
Redis: Basic C0 (250 MB)
Cosmos DB: Serverless
Storage: LRS (Local)
Costo: ~$50-100/mes
```

### **Staging**
```yaml
App Service: S1 Standard (1 instancia)
PostgreSQL: GP_Gen5_2 (2 vCores)
Redis: Standard C1 (1 GB)
Cosmos DB: 400 RU/s
Storage: GRS (Geo-redundant)
Costo: ~$200-300/mes
```

### **Production**
```yaml
App Service: P2V3 Premium (2-5 instancias con auto-scale)
PostgreSQL: GP_Gen5_4 (4 vCores + HA)
Redis: Premium P1 (6 GB + replication)
Cosmos DB: 400-1000 RU/s auto-scale
Storage: GRS + CDN
Costo: ~$1,200-1,600/mes
```

---

## 📞 Soporte y Mantenimiento

### **Azure Support Plan**
- **Recomendado**: Standard ($100/mes)
  - 24/7 technical support
  - SLA response: <1 hora (critical)
  - Arquitectura guidance

### **SLA (Service Level Agreements)**
```
App Service (Premium): 99.95%
PostgreSQL (HA): 99.99%
Redis (Premium): 99.9%
Cosmos DB: 99.99%
Front Door: 99.99%
Availability total: 99.9% uptime
```

### **Downtime anual máximo**: ~8.76 horas

---

## 📚 Documentación Adicional Necesaria

1. **`azure-deployment-guide.md`** - Guía paso a paso
2. **`azure-architecture.drawio`** - Diagrama visual
3. **`terraform/`** - Infrastructure as Code
4. **`pipelines/azure-pipelines.yml`** - CI/CD config
5. **`scripts/migrate-to-azure.sh`** - Script de migración
6. **`runbooks/disaster-recovery.md`** - DR procedures

---

## 🚦 Próximos Pasos Inmediatos

1. **Semana 1**: Aprobar arquitectura y presupuesto
2. **Semana 2**: Crear suscripción Azure y Resource Group
3. **Semana 3**: Provisionar infraestructura base
4. **Semana 4**: Migrar aplicación a staging
5. **Semana 5**: Testing exhaustivo
6. **Semana 6**: Go-live a producción

---

**¿Quieres que genere los scripts de Terraform, ARM templates, o la configuración de CI/CD con Azure DevOps?** 🚀
