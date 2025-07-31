# Sistema de Gestión de Prácticas Profesionales - API GraphQL

## 🚀 Descripción General

Este sistema utiliza **GraphQL** como API principal para la gestión de prácticas profesionales, implementado con **Arquitectura Hexagonal** y tecnologías avanzadas como Redis, JWT, y Celery.

## 📊 API GraphQL vs REST

### ¿Por qué GraphQL?

Para un proyecto de graduación en Ingeniería de Sistemas, GraphQL ofrece ventajas significativas:

1. **Flexibilidad de Consultas**: Los clientes pueden solicitar exactamente los datos que necesitan
2. **Reducción de Over-fetching**: No se transfieren datos innecesarios
3. **Fuerte Tipado**: Schema autodocumentado y validación automática
4. **Evolución de API**: Adición de campos sin versioning
5. **Herramientas de Desarrollo**: GraphiQL para testing interactivo

### Comparación con REST

| Aspecto | GraphQL | REST |
|---------|---------|------|
| Endpoints | 1 endpoint unificado | Múltiples endpoints |
| Datos | Consulta específica | Estructura fija |
| Versionado | Evolución del schema | Versioning de API |
| Caché | Complejo pero granular | Más sencillo |
| Learning Curve | Más empinada | Más familiar |

## 🏗️ Arquitectura GraphQL

```
src/adapters/primary/graphql_api/
├── __init__.py
├── types.py           # Definición de tipos GraphQL
├── queries.py         # Resolvers de consultas
├── mutations.py       # Resolvers de mutaciones
├── schema.py          # Schema principal
└── urls.py           # Configuración de endpoints
```

## 🔧 Configuración e Instalación

### 1. Paquetes GraphQL Instalados

```bash
pip install graphene-django django-filter django-graphql-jwt
```

### 2. Configuración en Django

En `config/settings.py`:

```python
INSTALLED_APPS = [
    # ... otras apps
    'graphene_django',
    'django_filters',
]

GRAPHENE = {
    'SCHEMA': 'src.adapters.primary.graphql_api.schema.schema',
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}

GRAPHQL_JWT = {
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_LONG_RUNNING_REFRESH_TOKEN': True,
    'JWT_ALLOW_ANY_CLASSES': [
        'graphql_jwt.mutations.ObtainJSONWebToken',
        'graphql_jwt.mutations.Verify',
        'graphql_jwt.mutations.Refresh',
    ],
}
```

### 3. URLs Configuradas

```python
# config/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    # API GraphQL (principal)
    path('api/', include('src.adapters.primary.graphql_api.urls')),
    # API REST (legacy/fallback)
    path('api/v1/', include('src.adapters.primary.rest_api.urls')),
]
```

## 📋 Tipos GraphQL Implementados

### Tipos Principales

1. **UserType**: Información de usuarios del sistema
2. **StudentType**: Datos específicos de estudiantes
3. **CompanyType**: Información de empresas
4. **SupervisorType**: Datos de supervisores
5. **PracticeType**: Información de prácticas profesionales
6. **DocumentType**: Documentos asociados a prácticas
7. **NotificationType**: Sistema de notificaciones

### Filtros Avanzados

- **Filtros por texto**: `nombre_icontains`, `email_exact`
- **Filtros por fecha**: `fecha_inicio_gte`, `fecha_fin_lte`
- **Filtros por estado**: `status_in`, `role_exact`
- **Filtros por relaciones**: `company__sector`, `student__carrera`

## 🔐 Sistema de Autenticación JWT

### Obtener Token

```graphql
mutation TokenAuth {
  tokenAuth(email: "usuario@ejemplo.com", password: "password") {
    token
    refreshToken
    user {
      id
      email
      role
    }
  }
}
```

### Usar Token en Headers

```http
Authorization: JWT eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## 📊 Queries Principales

### 1. Información del Usuario Actual

```graphql
query Me {
  me {
    id
    email
    firstName
    lastName
    role
    isActive
  }
}
```

### 2. Listar Prácticas con Filtros

```graphql
query AllPractices {
  practices(
    first: 10
    status: "IN_PROGRESS"
    company_Sector: "Tecnología"
  ) {
    edges {
      node {
        id
        titulo
        status
        student {
          codigoEstudiante
          user {
            firstName
            lastName
          }
        }
        company {
          nombre
          sector
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

### 3. Estadísticas del Sistema

```graphql
query SystemStats {
  statistics
}
```

## 🔄 Mutations Principales

### 1. Crear Práctica

```graphql
mutation CreatePractice($input: PracticeInput!) {
  createPractice(input: $input) {
    success
    message
    practice {
      id
      titulo
      status
    }
  }
}
```

### 2. Actualizar Estado de Práctica

```graphql
mutation UpdateStatus($practiceId: ID!, $status: String!) {
  updatePracticeStatus(practiceId: $practiceId, status: $status) {
    success
    message
    practice {
      id
      status
    }
  }
}
```

## 🛡️ Sistema de Permisos

### Control de Acceso por Roles

```python
@login_required
def resolve_practices(self, info, **kwargs):
    user = info.context.user
    if user.role in ['COORDINADOR', 'ADMINISTRADOR']:
        return Practice.objects.all()
    elif user.role == 'PRACTICANTE':
        return Practice.objects.filter(student__user=user)
    # ... más lógica de permisos
```

### Validaciones de Negocio

- **Estudiantes**: Solo pueden ver/modificar sus propias prácticas
- **Supervisores**: Acceso a prácticas de su empresa
- **Coordinadores**: Acceso completo con permisos de aprobación
- **Administradores**: Acceso total al sistema

## 🔍 Endpoints Disponibles

### GraphQL Principal
- **Desarrollo**: `http://localhost:8000/api/graphql/` (con GraphiQL)
- **Producción**: `http://localhost:8000/api/graphql/api/` (sin GraphiQL)

### REST (Legacy/Fallback)
- **Auth**: `http://localhost:8000/api/v1/auth/`
- **Users**: `http://localhost:8000/api/v1/users/`
- **Practices**: `http://localhost:8000/api/v1/practices/`

## 🧪 Testing GraphQL

### Usando GraphiQL (Desarrollo)

1. Navegar a `http://localhost:8000/api/graphql/`
2. Usar la interfaz interactiva para testing
3. Explorar schema con documentación automática

### Usando Postman/Insomnia

```http
POST /api/graphql/
Content-Type: application/json
Authorization: JWT your-token-here

{
  "query": "query { me { id email role } }",
  "variables": {}
}
```

## 📊 Ventajas para Proyecto de Graduación

### Aspectos Técnicos Avanzados

1. **Schema-First Development**: Definición clara de contratos de API
2. **Introspección**: Self-documenting API
3. **Performance**: Resolver pattern y N+1 query optimization
4. **Flexibilidad**: Adaptable a diferentes clients (web, mobile)

### Demostración de Conocimientos

- **Arquitectura Moderna**: GraphQL como tecnología emergente
- **Patrones de Diseño**: Repository, Use Case, Adapter patterns
- **Seguridad**: JWT, rate limiting, validación de permisos
- **Performance**: Caching, optimización de queries

## 🚀 Comandos de Desarrollo

### Ejecutar Servidor

```bash
python manage.py runserver
```

### Generar Schema

```bash
python manage.py graphql_schema --schema src.adapters.primary.graphql_api.schema.schema --out schema.json
```

### Testing

```bash
pytest tests/test_graphql/
```

## 📚 Recursos Adicionales

- [Documentación de Graphene-Django](https://docs.graphene-python.org/projects/django/)
- [Especificación GraphQL](https://spec.graphql.org/)
- [GraphQL Best Practices](https://graphql.org/learn/best-practices/)
- [JWT Authentication](https://django-graphql-jwt.domake.io/)

## 🎯 Próximos Pasos

1. **Implementar Subscriptions**: Para actualizaciones en tiempo real
2. **Optimizar Queries**: DataLoader para N+1 queries
3. **Rate Limiting**: Por usuario y por query complexity
4. **Monitoring**: Métricas de performance y uso
5. **Federation**: Microservicios con Apollo Federation
