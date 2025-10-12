# Modelos C4 - Sistema de Gestión de Prácticas Profesionales

## 📋 Resumen

Se han generado **modelos C4 completos** para el Sistema de Gestión de Prácticas Profesionales siguiendo la **Arquitectura Hexagonal**. Los modelos incluyen todos los 4 niveles de C4: **Context, Container, Component, y Code**.

## 🏗️ Arquitectura C4 Generada

### 1. **Context Level** - Vista del Sistema
- **5 Usuarios principales**: Estudiante, Supervisor, Coordinador, Secretaria, Administrador
- **3 Sistemas externos**: Sistema Académico UPEU, API SUNAT, Servicio de Email
- **1 Sistema principal**: Sistema de Gestión de Prácticas

### 2. **Container Level** - Aplicaciones y Servicios
- **Aplicación Web Django**: API REST + GraphQL con arquitectura hexagonal
- **PostgreSQL**: Base de datos principal para entidades
- **Redis**: Cache para sesiones y optimización
- **MongoDB**: Almacenamiento de documentos
- **Celery Worker**: Procesamiento de tareas asíncronas

### 3. **Component Level** - Arquitectura Hexagonal
#### Dominio (Core)
- **Entidades**: User, Student, Company, Supervisor, Practice
- **Value Objects**: Email, RUC, CodigoEstudiante, Telefono, Direccion
- **Enumeraciones**: UserRole, PracticeStatus, CompanyStatus

#### Puertos (Interfaces)
- **Puertos Primarios**: Interfaces para casos de uso
- **Puertos Secundarios**: Interfaces para repositorios y servicios

#### Aplicación
- **Casos de Uso**: Authentication, UserManagement, PracticeManagement
- **DTOs**: Data Transfer Objects

#### Adaptadores
- **Primarios**: REST API, GraphQL API
- **Secundarios**: Repositorios, Servicios de Seguridad, Cache, Logging

### 4. **Code Level** - Clases del Dominio
- **Jerarquía de Entidades**: Entity base class → User, Student, Company, etc.
- **Value Objects**: Objetos inmutables con validaciones
- **Enums**: Estados y roles del sistema

## 📁 Archivos Generados

```
docs/arquitectura/
├── c4_models_sistema_practicas.json     # Modelos C4 completos en JSON
├── C4_Documentation.md                  # Documentación completa
├── c4_models_generator.py              # Generador independiente
├── c4_models_structurizr.py           # Generador con Structurizr
├── django_c4_endpoint.py              # Código de ejemplo para endpoint
└── c4_diagrams/                       # Diagramas PlantUML
    ├── SystemContext.puml              # Diagrama de Contexto
    ├── Containers.puml                 # Diagrama de Contenedores
    ├── Components.puml                 # Diagrama de Componentes
    └── DomainClasses.puml             # Diagrama de Código
```

## 🌐 Endpoints Django Implementados

Se han creado **endpoints RESTful** para servir los modelos C4:

### Rutas Disponibles

```bash
# Modelos C4 completos
GET /api/v1/c4/models/

# Diagramas específicos (JSON)
GET /api/v1/c4/diagrams/{type}/
# Tipos: context, containers, components, code

# Diagramas PlantUML (texto plano)
GET /api/v1/c4/diagrams/{type}/raw/

# Metadatos del sistema
GET /api/v1/c4/metadata/
```

### Archivos de Implementación

```
src/adapters/primary/rest_api/
├── views/c4_views.py                   # Vistas API implementadas
└── urls/c4_urls.py                     # URLs configuradas
```

## 🚀 Cómo Usar

### 1. **Visualizar Diagramas**
```bash
# Instalar extensión PlantUML en VS Code
# Abrir archivos .puml para ver los diagramas
code docs/arquitectura/c4_diagrams/SystemContext.puml
```

### 2. **Ejecutar Generador**
```bash
cd docs/arquitectura/
python c4_models_generator.py
```

### 3. **Usar Endpoints API**
```bash
# Obtener modelos completos (requiere autenticación)
curl -H "Authorization: Bearer $TOKEN" \\
     http://localhost:8000/api/v1/c4/models/

# Obtener diagrama de contexto
curl -H "Authorization: Bearer $TOKEN" \\
     http://localhost:8000/api/v1/c4/diagrams/context/

# Obtener PlantUML para visualizador
curl http://localhost:8000/api/v1/c4/diagrams/context/raw/
```

### 4. **Integrar con Frontend**
```javascript
// Obtener modelos C4
const response = await fetch('/api/v1/c4/models/', {
    headers: { 'Authorization': `Bearer ${token}` }
});
const c4Models = await response.json();

// Obtener diagrama específico
const diagramResponse = await fetch('/api/v1/c4/diagrams/context/');
const diagram = await diagramResponse.json();
```

## 🎯 Características Principales

### ✅ **Arquitectura Hexagonal Completa**
- Separación clara entre dominio, aplicación e infraestructura
- Puertos e interfaces bien definidos
- Inversión de dependencias implementada

### ✅ **Modelos C4 Completos**
- **Context**: Usuarios y sistemas externos
- **Container**: Aplicaciones y servicios
- **Component**: Arquitectura interna
- **Code**: Clases del dominio

### ✅ **Endpoints RESTful**
- APIs seguras con autenticación JWT
- Cache implementado para optimización
- Respuestas JSON estructuradas
- Manejo de errores robusto

### ✅ **Documentación Automática**
- PlantUML para visualización
- Markdown para documentación
- JSON para integración programática

### ✅ **Sin Dependencias Externas**
- Generador independiente en Python puro
- Compatible con cualquier entorno
- Fácil de mantener y extender

## 🔧 Configuración de Structurizr (Opcional)

Para usar Structurizr online:

```python
# Instalar dependencia
pip install structurizr-python

# Configurar y subir
from docs.arquitectura.c4_models_structurizr import create_c4_models, upload_to_structurizr

workspace = create_c4_models()
upload_to_structurizr(workspace, 'api_key', 'api_secret', workspace_id)
```

## 📊 Estadísticas del Modelo

- **Personas**: 5 (roles de usuario)
- **Sistemas de Software**: 4 (1 interno, 3 externos)
- **Contenedores**: 5 (app, 3 BDs, worker)
- **Componentes**: 15 (siguiendo arquitectura hexagonal)
- **Elementos de Código**: 16 (entidades, VOs, enums, DTOs)
- **Relaciones**: 40+ (conexiones entre elementos)

## 🎨 Estilos y Visualización

Los diagramas incluyen:
- **Colores diferenciados** por tipo de elemento
- **Iconos específicos** para personas, sistemas, BDs
- **Agrupación lógica** por capas arquitectónicas
- **Leyendas explicativas** en cada diagrama

## 📝 Próximos Pasos

1. **Visualizar** los diagramas en VS Code con PlantUML
2. **Revisar** la documentación generada
3. **Probar** los endpoints en el servidor Django
4. **Personalizar** los modelos según necesidades específicas
5. **Integrar** con herramientas de documentación existentes

---

**🎉 ¡Los modelos C4 han sido generados exitosamente y están listos para usar!**