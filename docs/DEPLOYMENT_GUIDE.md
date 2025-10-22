# 🚀 Guía de Deployment - Sistema PPP UPeU

## 📋 Resumen Ejecutivo

Esta guía documenta el proceso completo de deployment del Sistema de Gestión de Prácticas Profesionales de la Universidad Peruana Unión (UPeU). El sistema utiliza una arquitectura de microservicios containerizada con Docker, implementando una distribución híbrida de datos entre PostgreSQL, MongoDB y Redis.

## 🏗️ Arquitectura de Deployment

### Stack Tecnológico

```mermaid
graph TB
    subgraph "Frontend"
        A[Django Templates + GraphQL Playground]
    end
    
    subgraph "Backend Services"
        B[Django App + DRF + GraphQL]
        C[Celery Worker]
        D[Celery Beat]
    end
    
    subgraph "Data Layer"
        E[PostgreSQL - Datos Relacionales]
        F[MongoDB - Documentos y Logs]
        G[Redis - Cache y Sesiones]
    end
    
    A --> B
    B --> E
    B --> F
    B --> G
    C --> E
    C --> F
    C --> G
    D --> C
```

### Distribución de Datos

| Base de Datos | Propósito | Datos Almacenados |
|---------------|-----------|-------------------|
| **PostgreSQL** | Datos relacionales críticos | • 23 tablas core del sistema<br>• 9 tablas de seguridad<br>• Usuarios, empresas, prácticas<br>• Auditoría y logs de seguridad |
| **MongoDB** | Documentos y logs flexibles | • Almacenamiento de archivos<br>• Logs de GraphQL<br>• Métricas del sistema<br>• Notificaciones temporales<br>• Cache de schemas |
| **Redis** | Cache y sesiones | • Sesiones de usuario<br>• Cache de queries<br>• Cola de tareas Celery<br>• Rate limiting |

## 🐳 Contenedores Docker

### Servicios Configurados

1. **django_app**: Aplicación principal Django con DRF y GraphQL
2. **postgres_db**: Base de datos PostgreSQL 15
3. **mongodb**: Base de datos MongoDB 6.0
4. **redis_cache**: Cache Redis 7.0
5. **celery_worker**: Procesador de tareas asíncronas
6. **celery_beat**: Programador de tareas periódicas

### Red y Volúmenes

- **Red privada**: `172.20.0.0/16` para comunicación interna segura
- **Volúmenes persistentes**: 
  - `postgres_data`: Datos de PostgreSQL
  - `mongodb_data`: Datos de MongoDB
  - `redis_data`: Datos de Redis
  - `media_files`: Archivos subidos
  - `static_files`: Archivos estáticos

## 🚀 Proceso de Deployment

### Prerrequisitos

1. **Docker** (v20.10+)
2. **Docker Compose** (v2.0+)
3. **Sistema Operativo**: Linux/macOS/Windows
4. **RAM mínima**: 4GB
5. **Espacio en disco**: 10GB

### Opción 1: Deployment Automático (Recomendado)

#### Linux/macOS:
```bash
# Hacer ejecutable el script
chmod +x init_system.sh

# Ejecutar inicialización completa
./init_system.sh
```

#### Windows PowerShell:
```powershell
# Ejecutar como administrador
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Inicialización completa
.\init_system.ps1

# Con limpieza previa (opcional)
.\init_system.ps1 -CleanStart
```

### Opción 2: Deployment Manual

#### 1. Configuración de Variables de Entorno
```bash
# Copiar y personalizar archivo de entorno
cp .env.example .env
# Editar .env con los valores específicos de tu entorno
```

#### 2. Construcción de Imágenes
```bash
docker-compose build django_app
```

#### 3. Inicialización de Bases de Datos
```bash
# Iniciar servicios de BD
docker-compose up -d postgres_db mongodb redis_cache

# Esperar a que estén listos (verificar con docker-compose ps)

# Inicializar PostgreSQL
docker-compose exec -T postgres_db psql -U upeu_admin -d upeu_ppp_db < docs/arquitectura/database_schema.sql
docker-compose exec -T postgres_db psql -U upeu_admin -d upeu_ppp_db < docs/arquitectura/seguridad_tablas.sql

# Inicializar MongoDB
docker-compose exec -T mongodb mongosh upeu_documents < docs/arquitectura/mongodb_init.js
```

#### 4. Inicialización de Django
```bash
# Iniciar aplicación
docker-compose up -d django_app

# Ejecutar migraciones
docker-compose exec django_app python manage.py migrate

# Crear superusuario
docker-compose exec django_app python manage.py createsuperuser
```

#### 5. Inicialización de Celery
```bash
docker-compose up -d celery_worker celery_beat
```

## 🔒 Configuración de Seguridad

### Características de Seguridad Implementadas

1. **Autenticación JWT**
   - Tokens de acceso (15 min)
   - Tokens de refresh (7 días)
   - Blacklist automática

2. **Rate Limiting**
   - 60 requests/minuto por IP
   - 1000 requests/hora por IP
   - Blacklist automática tras 10 violaciones

3. **Auditoría Completa**
   - Log de todos los accesos
   - Seguimiento de cambios críticos
   - Análisis de patrones de seguridad

4. **GraphQL Security**
   - Limitación de profundidad de queries
   - Limitación de complejidad
   - Monitoreo de performance

### Variables de Seguridad Principales

```env
# JWT Configuration
JWT_SECRET_KEY=<clave-secreta-64-chars>
JWT_ACCESS_TOKEN_LIFETIME=15
JWT_REFRESH_TOKEN_LIFETIME=7

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
BLACKLIST_THRESHOLD=10

# GraphQL Security
GRAPHQL_MAX_QUERY_DEPTH=10
GRAPHQL_MAX_QUERY_COMPLEXITY=1000
```

## 📊 Monitoreo y Métricas

### Logs Disponibles

1. **Logs de aplicación**:
   ```bash
   docker-compose logs -f django_app
   ```

2. **Logs de base de datos**:
   ```bash
   docker-compose logs -f postgres_db
   docker-compose logs -f mongodb
   ```

3. **Logs de Celery**:
   ```bash
   docker-compose logs -f celery_worker
   docker-compose logs -f celery_beat
   ```

### Health Checks

El sistema incluye health checks automáticos para todos los servicios:

- **Django**: `/health/` endpoint
- **PostgreSQL**: `pg_isready` check
- **MongoDB**: `mongosh ping` check
- **Redis**: `redis-cli ping` check

### Métricas en MongoDB

Las métricas se almacenan automáticamente en MongoDB:

```javascript
// Consultar métricas de performance
db.system_metrics.find({"metric_type": "performance"}).sort({"timestamp": -1}).limit(10)

// Consultar logs de GraphQL
db.graphql_logs.find({"errors": {$exists: true}}).sort({"timestamp": -1})

// Estadísticas de uso
db.runCommand("getUsageStats", 30) // Últimos 30 días
```

## 🔧 Comandos de Mantenimiento

### Backup de Datos

```bash
# Backup PostgreSQL
docker-compose exec postgres_db pg_dump -U upeu_admin upeu_ppp_db > backup_postgres_$(date +%Y%m%d_%H%M%S).sql

# Backup MongoDB
docker-compose exec mongodb mongodump --db upeu_documents --out /backup/mongodb_$(date +%Y%m%d_%H%M%S)

# Backup Redis
docker-compose exec redis_cache redis-cli BGSAVE
```

### Restauración de Datos

```bash
# Restaurar PostgreSQL
docker-compose exec -T postgres_db psql -U upeu_admin -d upeu_ppp_db < backup_postgres.sql

# Restaurar MongoDB
docker-compose exec mongodb mongorestore --db upeu_documents /backup/mongodb_backup/

# Restaurar Redis (reiniciar con RDB file)
docker-compose restart redis_cache
```

### Limpieza y Mantenimiento

```bash
# Limpiar datos de desarrollo
docker-compose down -v --remove-orphans

# Limpiar imágenes no utilizadas
docker system prune -a

# Ver uso de espacio
docker system df

# Logs de MongoDB (limpiar antiguos)
docker-compose exec mongodb mongo upeu_documents --eval "db.graphql_logs.deleteMany({'timestamp': {\$lt: new Date(Date.now() - 30*24*60*60*1000)}})"
```

## 🌐 URLs y Endpoints

Una vez deployado, el sistema estará disponible en:

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Aplicación Web** | http://localhost:8000 | Interfaz principal |
| **Admin Django** | http://localhost:8000/admin | Panel administrativo |
| **API REST** | http://localhost:8000/api/v1/ | Endpoints REST |
| **GraphQL** | http://localhost:8000/graphql | API GraphQL + Playground |
| **Health Check** | http://localhost:8000/health/ | Estado del sistema |

### Credenciales por Defecto

| Servicio | Usuario | Contraseña |
|----------|---------|------------|
| **Django Admin** | admin | UPeU2024Admin! |
| **PostgreSQL** | upeu_admin | UPeU2024_Secure! |
| **MongoDB** | django_app | django_mongo_secure_2024 |

## 🚨 Troubleshooting

### Problemas Comunes

1. **Puerto ya en uso**:
   ```bash
   # Cambiar puertos en docker-compose.yml
   ports:
     - "8001:8000"  # En lugar de 8000:8000
   ```

2. **Memoria insuficiente**:
   ```bash
   # Reducir workers de Celery
   docker-compose up -d --scale celery_worker=1
   ```

3. **Problemas de permisos**:
   ```bash
   # Linux/macOS
   sudo chown -R $USER:$USER .
   
   # Windows
   # Ejecutar PowerShell como administrador
   ```

4. **Base de datos no responde**:
   ```bash
   # Reiniciar servicios de BD
   docker-compose restart postgres_db mongodb redis_cache
   ```

### Logs de Diagnóstico

```bash
# Ver todos los logs
docker-compose logs

# Ver logs específicos con follow
docker-compose logs -f django_app

# Ver últimas 100 líneas
docker-compose logs --tail=100 postgres_db

# Ver logs por timestamp
docker-compose logs --since="2024-01-01T00:00:00Z"
```

## 📈 Escalabilidad y Performance

### Configuraciones de Performance

1. **PostgreSQL Tuning**:
   ```sql
   -- Configuraciones recomendadas para producción
   ALTER SYSTEM SET shared_buffers = '256MB';
   ALTER SYSTEM SET effective_cache_size = '1GB';
   ALTER SYSTEM SET maintenance_work_mem = '64MB';
   ```

2. **MongoDB Indexing**:
   - 23 índices automáticos creados
   - TTL para limpieza automática
   - Sharding preparado para crecimiento

3. **Redis Configuration**:
   - Maxmemory policy: allkeys-lru
   - Persistent: RDB snapshots
   - Memoria máxima: 256MB

### Escalamiento Horizontal

```bash
# Escalar workers de Celery
docker-compose up -d --scale celery_worker=3

# Monitorear recursos
docker stats

# Load balancer (configuración futura)
# nginx + múltiples instancias de django_app
```

## 🔐 Configuración de Producción

### Variables de Entorno para Producción

```env
# Seguridad
DEBUG=False
SECRET_KEY=<clave-super-secreta-produccion>
ALLOWED_HOSTS=dominio.upeu.edu.pe,www.dominio.upeu.edu.pe

# SSL/TLS
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=sistema.ppp@upeu.edu.pe
EMAIL_HOST_PASSWORD=<password-aplicacion>

# Database Production URLs
DATABASE_URL=postgresql://user:pass@production-host:5432/dbname
MONGODB_URL=mongodb://user:pass@production-host:27017/dbname
REDIS_URL=redis://user:pass@production-host:6379/0
```

### Recomendaciones de Producción

1. **Reverse Proxy**: Nginx o Apache
2. **SSL Certificate**: Let's Encrypt o certificado corporativo
3. **Database**: Instancias separadas y replicadas
4. **Monitoring**: Prometheus + Grafana
5. **Backup**: Automatizado diario con retención
6. **Logs**: Centralizados con ELK Stack

## 📞 Soporte y Mantenimiento

### Contactos

- **Desarrollador**: Sistema desarrollado para UPeU
- **Documentación**: Este archivo y `/docs/`
- **Issues**: GitHub repository issues

### Actualizaciones

1. **Backup** antes de actualizar
2. **Testear** en ambiente de desarrollo
3. **Aplicar migraciones** en orden
4. **Verificar** funcionamiento post-actualización

---

**Última actualización**: Diciembre 2024  
**Versión del sistema**: 1.0.0  
**Compatibilidad**: Docker 20.10+, Python 3.11+, Django 5.0+