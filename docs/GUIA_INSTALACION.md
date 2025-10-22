# 📦 Guía de Instalación - Sistema de Gestión de Prácticas Profesionales

## 🎯 Requisitos Previos

### Software Necesario

- **Python**: 3.10 o superior
- **PostgreSQL**: 13 o superior
- **Redis**: 6.0 o superior (opcional, para cache)
- **MongoDB**: 5.0 o superior (opcional, para logs)
- **Git**: Para clonar el repositorio
- **Node.js**: 16+ (opcional, para frontend)

### Verificar Versiones

```bash
python --version    # Python 3.10+
psql --version      # PostgreSQL 13+
redis-server --version  # Redis 6.0+
git --version
```

---

## 🚀 Instalación Rápida (Desarrollo)

### 1. Clonar Repositorio

```bash
git clone https://github.com/AaronAP1/DJGRedis.PA.git
cd DJGRedis.PA
```

### 2. Crear Entorno Virtual

**Linux/Mac**:
```bash
python -m venv venv
source venv/bin/activate
```

**Windows**:
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
# Dependencias base
pip install -r requirements/base.txt

# Desarrollo (incluye testing, linting)
pip install -r requirements/development.txt

# O mínimas (solo lo esencial)
pip install -r requirements/minimal.txt
```

### 4. Configurar Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```bash
# .env
DEBUG=True
SECRET_KEY=tu-secret-key-super-segura-aqui
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_NAME=practicas_db
DATABASE_USER=postgres
DATABASE_PASSWORD=tu_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Redis (opcional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Email (opcional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password
EMAIL_USE_TLS=True

# JWT
JWT_SECRET_KEY=otra-clave-secreta
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60
```

### 5. Configurar Base de Datos

```bash
# Crear base de datos PostgreSQL
createdb practicas_db

# O usando psql
psql -U postgres
CREATE DATABASE practicas_db;
\q
```

### 6. Ejecutar Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Crear Superusuario

```bash
python manage.py createsuperuser
```

Ingresa:
- Email: admin@upeu.edu.pe
- Password: (tu password seguro)
- Nombre: Admin
- Apellido: Sistema

### 8. Cargar Datos Iniciales (Opcional)

```bash
# Si existen fixtures
python manage.py loaddata initial_data.json
```

### 9. Iniciar Servidor

```bash
python manage.py runserver
```

Accede a:
- **Aplicación**: http://localhost:8000
- **Admin**: http://localhost:8000/admin/
- **API Docs**: http://localhost:8000/api/docs/
- **GraphQL**: http://localhost:8000/graphql/

---

## 🐳 Instalación con Docker

### 1. Requisitos

- Docker Desktop (Windows/Mac) o Docker Engine (Linux)
- docker-compose

### 2. Construir y Ejecutar

```bash
# Construir imágenes
docker-compose build

# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f web

# Ejecutar migraciones
docker-compose exec web python manage.py migrate

# Crear superusuario
docker-compose exec web python manage.py createsuperuser
```

### 3. Acceder

- **Aplicación**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 4. Detener Servicios

```bash
docker-compose down

# Con volúmenes (elimina datos)
docker-compose down -v
```

---

## 🔧 Configuración Avanzada

### Redis (Cache y Sesiones)

1. **Instalar Redis**:

**Ubuntu**:
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
```

**Windows**: Descargar de https://github.com/microsoftarchive/redis/releases

**Mac**:
```bash
brew install redis
brew services start redis
```

2. **Verificar**:
```bash
redis-cli ping
# PONG
```

3. **Configurar en Django** (`config/settings.py`):
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### MongoDB (Logs Opcionales)

1. **Instalar MongoDB**:

**Ubuntu**:
```bash
wget -qO - https://www.mongodb.org/static/pgp/server-5.0.asc | sudo apt-key add -
sudo apt install mongodb-org
sudo systemctl start mongod
```

**Windows**: Descargar de https://www.mongodb.com/try/download/community

**Mac**:
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

2. **Verificar**:
```bash
mongosh
# MongoDB shell version
```

### Celery (Tareas Asíncronas)

1. **Iniciar Worker**:
```bash
celery -A config worker -l info
```

2. **Iniciar Beat (tareas programadas)**:
```bash
celery -A config beat -l info
```

3. **Flower (Monitor Web)**:
```bash
celery -A config flower
# http://localhost:5555
```

---

## 📊 Verificación de Instalación

### Script de Verificación

```bash
python scripts/verify_installation.py
```

### Verificación Manual

```bash
# 1. Migraciones aplicadas
python manage.py showmigrations

# 2. Tests funcionando
python manage.py test

# 3. Servidor corriendo
curl http://localhost:8000/api/v1/

# 4. Redis conectado (si instalado)
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'ok')
>>> cache.get('test')
'ok'
```

---

## 🌐 Habilitar REST API v2

En `config/urls.py`, descomentar:

```python
# ========================================================================
# REST API v2 (ViewSets completos - Fase 3 + Dashboards Fase 7)
# ========================================================================
path('api/v2/', include('src.adapters.primary.rest_api.urls_api_v2')),
```

Reiniciar servidor:
```bash
python manage.py runserver
```

---

## 📦 Dependencias Opcionales

### Para Exportación Excel

```bash
pip install openpyxl
```

### Para Generación PDF

```bash
pip install reportlab
pip install weasyprint
```

### Para Testing Avanzado

```bash
pip install pytest-django
pip install factory-boy
pip install faker
```

### Para Análisis de Código

```bash
pip install pylint
pip install black
pip install flake8
```

---

## 🔒 Configuración de Seguridad

### Generar SECRET_KEY

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### Configurar CORS (si usas frontend separado)

En `config/settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React
    "http://localhost:8080",  # Vue
    "http://localhost:4200",  # Angular
]

CORS_ALLOW_CREDENTIALS = True
```

### HTTPS en Producción

```python
# Solo en producción
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## 🧪 Ejecutar Tests

```bash
# Todos los tests
python manage.py test

# Tests específicos
python manage.py test tests.test_auth_flows

# Con pytest
pytest

# Con cobertura
pytest --cov=src --cov-report=html
```

---

## 📝 Crear Datos de Prueba

### Script de Población

```bash
python manage.py shell
```

```python
from src.domain.models import User, Student, Company
from decimal import Decimal

# Crear estudiante
user = User.objects.create_user(
    email='estudiante@upeu.edu.pe',
    password='test123',
    first_name='Juan',
    last_name='Pérez',
    role='PRACTICANTE'
)

student = Student.objects.create(
    user=user,
    codigo_estudiante='2024012345',
    escuela_profesional='Ingeniería de Sistemas',
    semestre_actual=7,
    promedio_ponderado=Decimal('15.5')
)

# Crear empresa
company = Company.objects.create(
    razon_social='TechCorp SAC',
    ruc='20123456789',
    sector_economico='Tecnología',
    direccion='Av. Ejemplo 123',
    telefono='987654321',
    email='contacto@techcorp.com',
    validated=True,
    estado='ACTIVE'
)

print("✅ Datos de prueba creados")
```

---

## 🐛 Troubleshooting

### Error: "Module not found"

```bash
# Reinstalar dependencias
pip install -r requirements/base.txt --upgrade
```

### Error: "Database does not exist"

```bash
# Crear base de datos
createdb practicas_db
python manage.py migrate
```

### Error: "Port already in use"

```bash
# Usar otro puerto
python manage.py runserver 8001
```

### Error: "Redis connection refused"

```bash
# Verificar que Redis esté corriendo
redis-cli ping

# Iniciar Redis
# Linux/Mac: redis-server
# Windows: Iniciar desde servicios
```

### Error: "Permission denied"

**Linux/Mac**:
```bash
chmod +x manage.py
```

### Limpiar Base de Datos

```bash
# Eliminar migraciones
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# Eliminar base de datos
dropdb practicas_db
createdb practicas_db

# Recrear migraciones
python manage.py makemigrations
python manage.py migrate
```

---

## 📊 Comandos Útiles

```bash
# Ver rutas disponibles
python manage.py show_urls

# Shell interactivo
python manage.py shell

# Crear app nueva
python manage.py startapp nombre_app

# Colectar archivos estáticos
python manage.py collectstatic

# Limpiar sesiones expiradas
python manage.py clearsessions

# Verificar configuración
python manage.py check

# Información del sistema
python manage.py diffsettings
```

---

## 🎓 Próximos Pasos

1. ✅ Instalación completada
2. ✅ Servidor corriendo
3. 📚 Leer [Guía de Usuario](GUIA_USUARIO.md)
4. 🔧 Leer [Guía de Desarrollo](GUIA_DESARROLLO.md)
5. 🚀 Leer [Guía de Deployment](DEPLOYMENT_GUIDE.md)
6. 📖 Explorar [API Documentation](http://localhost:8000/api/docs/)

---

## 📞 Soporte

- **Documentación**: `/docs/`
- **Issues**: GitHub Issues
- **Email**: soporte@upeu.edu.pe

---

**Universidad Peruana Unión** - Sistema de Gestión de Prácticas Profesionales  
**Versión**: 2.0  
**Última actualización**: Octubre 2024
