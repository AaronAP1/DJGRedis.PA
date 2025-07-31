# Sistema de Gestión de Prácticas Profesionales

Un sistema completo para la gestión de prácticas profesionales desarrollado con **Django** y **Arquitectura Hexagonal**.

## 🏗️ Arquitectura

Este proyecto implementa **Arquitectura Hexagonal (Ports and Adapters)** con las siguientes capas:

### 📁 Estructura del Proyecto

```
gestion_practicas_backend/
├── 📂 src/
│   ├── 📂 domain/                    # 🎯 DOMINIO
│   │   ├── entities.py               # Entidades de negocio
│   │   ├── value_objects.py          # Objetos de valor
│   │   └── enums.py                  # Enumeraciones
│   │
│   ├── 📂 ports/                     # 🔌 PUERTOS (INTERFACES)
│   │   ├── primary/                  # APIs de entrada
│   │   └── secondary/                # Servicios externos
│   │
│   ├── 📂 adapters/                  # 🔧 ADAPTADORES
│   │   ├── primary/                  # API REST, GraphQL, WebSockets
│   │   └── secondary/                # Base de datos, caché, email
│   │
│   └── 📂 application/               # 🚀 APLICACIÓN
│       ├── use_cases/                # Casos de uso
│       └── dto.py                    # Data Transfer Objects
│
├── 📂 config/                        # ⚙️ CONFIGURACIÓN DJANGO
├── 📂 requirements/                  # 📦 DEPENDENCIAS
└── 📄 docker-compose.yml            # 🐳 CONTENEDORES
```

## 👥 Roles del Sistema

El sistema maneja 5 roles principales:

- **PRACTICANTE**: Estudiantes realizando prácticas
- **SUPERVISOR**: Supervisores de empresas
- **COORDINADOR**: Coordinadores académicos
- **SECRETARIA**: Personal administrativo
- **ADMINISTRADOR**: Administradores del sistema

## 🛠️ Stack Tecnológico

### Backend Core
- **Django 5.0+**: Framework principal
- **Django REST Framework**: API REST
- **PostgreSQL**: Base de datos principal
- **Redis**: Cache y sesiones
- **Celery**: Tareas asíncronas

### Seguridad
- **JWT**: Autenticación stateless
- **Django Axes**: Protección brute force
- **Rate Limiting**: Control de acceso
- **Encriptación**: Datos sensibles

### Performance y Escalabilidad
- **Docker**: Containerización
- **Gunicorn**: Servidor WSGI
- **Nginx**: Reverse proxy
- **Elasticsearch**: Búsqueda avanzada

### Monitoreo
- **Sentry**: Tracking de errores
- **Flower**: Monitoreo de Celery
- **Logging estructurado**: JSON logs

## 🚀 Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd gestion_practicas_backend
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### 3. Usando Docker (Recomendado)
```bash
# Construir y levantar todos los servicios
docker-compose up --build

# Ejecutar migraciones
docker-compose exec web python manage.py migrate

# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Cargar datos iniciales (opcional)
docker-compose exec web python manage.py loaddata fixtures/initial_data.json
```

### 4. Instalación local (Desarrollo)
```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements/development.txt

# Configurar base de datos
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor de desarrollo
python manage.py runserver
```

## 📊 Servicios y Puertos

| Servicio | Puerto | Descripción |
|----------|---------|-------------|
| Django Web | 8000 | Aplicación principal |
| PostgreSQL | 5432 | Base de datos |
| Redis | 6379 | Cache y broker |
| MongoDB | 27017 | Logs y métricas |
| Elasticsearch | 9200 | Motor de búsqueda |
| Flower | 5555 | Monitoreo Celery |
| Nginx | 80/443 | Reverse proxy |

## 🔧 Comandos Útiles

### Django
```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recopilar archivos estáticos
python manage.py collectstatic

# Shell de Django
python manage.py shell_plus
```

### Celery
```bash
# Iniciar worker
celery -A config worker -l info

# Iniciar beat scheduler
celery -A config beat -l info

# Monitorear con Flower
celery -A config flower
```

### Docker
```bash
# Ver logs
docker-compose logs -f web

# Ejecutar comandos en contenedor
docker-compose exec web python manage.py migrate

# Reiniciar servicios
docker-compose restart

# Limpiar todo
docker-compose down -v
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Tests con cobertura
pytest --cov=src

# Tests específicos
pytest src/tests/test_users.py

# Tests en paralelo
pytest -n auto
```

## 📈 Monitoreo y Logs

### Logs estructurados
Los logs se generan en formato JSON y se almacenan en:
- `logs/django.log`: Logs de la aplicación
- `logs/security.log`: Eventos de seguridad

### Métricas
- **Prometheus**: Métricas de aplicación
- **Flower**: Monitoreo de tareas Celery
- **Django Admin**: Panel administrativo

## 🔒 Seguridad

### Funcionalidades implementadas:
- ✅ Autenticación JWT con refresh tokens
- ✅ Rate limiting por IP y usuario
- ✅ Protección contra brute force
- ✅ Encriptación de datos sensibles
- ✅ Validación de inputs
- ✅ Logging de eventos de seguridad
- ✅ Headers de seguridad
- ✅ CORS configurado

## 📚 API Documentation

La documentación de la API está disponible en:
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`

### Endpoints principales:
```
POST /api/v1/auth/login/          # Autenticación
GET  /api/v1/users/               # Listar usuarios
POST /api/v1/students/            # Crear estudiante
GET  /api/v1/practices/           # Listar prácticas
POST /api/v1/companies/           # Crear empresa
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -am 'Agregar nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

## 👨‍💻 Autor

Desarrollado como proyecto de graduación en Ingeniería de Sistemas.

---

**Nota**: Este es un proyecto académico que demuestra conocimientos avanzados en:
- Arquitectura de software (Hexagonal)
- Patrones de diseño
- Seguridad en aplicaciones web
- Escalabilidad y performance
- DevOps y containerización
- Testing y calidad de código
