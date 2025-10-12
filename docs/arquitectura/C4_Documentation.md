# Sistema de Gestión de Prácticas Profesionales

Sistema para gestión integral de prácticas profesionales universitarias

**Versión:** 1.0.0  
**Fecha de creación:** 2025-09-30T19:06:56.134096

## Arquitectura C4 Model

### Nivel 1: Contexto del Sistema

El sistema de gestión de prácticas profesionales es una aplicación web que permite gestionar de manera integral el proceso de prácticas profesionales universitarias.

#### Usuarios del Sistema:
- **Estudiante**: Registra y gestiona sus prácticas profesionales
- **Supervisor de Empresa**: Supervisa y evalúa a los practicantes
- **Coordinador Académico**: Aprueba y supervisa el proceso académico
- **Secretaria Académica**: Gestiona documentación y valida requisitos
- **Administrador del Sistema**: Administra usuarios y configura el sistema

#### Sistemas Externos:
- **Sistema Académico UPEU**: Proporciona datos académicos de estudiantes
- **API SUNAT**: Valida información de empresas mediante RUC
- **Servicio de Email**: Envía notificaciones por correo electrónico

### Nivel 2: Contenedores

#### Aplicación Web Django
- **Tecnología**: Python, Django 5.0, Django REST Framework, Graphene
- **Función**: Aplicación principal con arquitectura hexagonal
- **APIs**: REST API y GraphQL API

#### Almacenamiento de Datos
- **PostgreSQL**: Base de datos principal para entidades del dominio
- **Redis**: Cache para sesiones, tokens JWT y optimización
- **MongoDB**: Almacenamiento de documentos y archivos

#### Procesamiento Asíncrono
- **Celery Worker**: Procesa tareas en segundo plano como envío de emails y validaciones

### Nivel 3: Componentes (Arquitectura Hexagonal)

#### Dominio (Core)
- **Entidades**: User, Student, Company, Supervisor, Practice
- **Value Objects**: Email, RUC, CodigoEstudiante, Telefono, Direccion
- **Enumeraciones**: UserRole, PracticeStatus, CompanyStatus

#### Puertos (Interfaces)
- **Puertos Primarios**: Interfaces para casos de uso (Driving Adapters)
- **Puertos Secundarios**: Interfaces para repositorios y servicios (Driven Adapters)

#### Aplicación
- **Casos de Uso**: AuthenticationUseCase, UserManagementUseCase, PracticeManagementUseCase
- **DTOs**: Data Transfer Objects para comunicación entre capas

#### Adaptadores Primarios (Web Layer)
- **REST API**: Endpoints para operaciones CRUD
- **GraphQL API**: Consultas flexibles y eficientes

#### Adaptadores Secundarios (Infrastructure)
- **Repositorios**: Implementaciones de persistencia
- **Servicios**: Security, Cache, Logging
- **Middleware**: Authentication, Rate Limiting

### Nivel 4: Código

#### Entidades Principales

**User (Usuario)**
- Entidad base para todos los usuarios del sistema
- Roles: PRACTICANTE, SUPERVISOR, COORDINADOR, SECRETARIA, ADMINISTRADOR
- Funciones: autenticación, autorización, gestión de perfiles

**Student (Estudiante)**
- Extiende User con información académica
- Validaciones: semestre mínimo (6to), promedio mínimo (12.0)
- Funciones: gestión de datos académicos, elegibilidad para prácticas

**Company (Empresa)**
- Información de empresas que reciben practicantes
- Validación: RUC válido, estado activo
- Estados: PENDING_VALIDATION, ACTIVE, SUSPENDED, INACTIVE

**Practice (Práctica)**
- Entidad central del sistema
- Estados: DRAFT → PENDING → APPROVED → IN_PROGRESS → COMPLETED
- Validaciones: supervisor asignado, empresa activa, horas mínimas

## Principios de Arquitectura Hexagonal

### Separación de Responsabilidades
- **Dominio**: Lógica de negocio pura, sin dependencias externas
- **Aplicación**: Casos de uso que coordinan el dominio
- **Infraestructura**: Detalles técnicos (BD, APIs, frameworks)

### Inversión de Dependencias
- El dominio no depende de infraestructura
- La infraestructura depende del dominio
- Uso de interfaces (puertos) para desacoplar

### Adaptadores
- **Primarios**: Reciben requests del exterior (REST, GraphQL)
- **Secundarios**: Acceden a recursos externos (BD, APIs, email)

## Patrones de Diseño Utilizados

- **Repository Pattern**: Abstracción del acceso a datos
- **Use Case Pattern**: Encapsulación de lógica de aplicación
- **DTO Pattern**: Transferencia de datos entre capas
- **Value Object Pattern**: Objetos inmutables con validaciones
- **Factory Pattern**: Creación de entidades complejas

## Seguridad

- **Autenticación**: JWT tokens con refresh
- **Autorización**: Role-based access control (RBAC)
- **Validación**: Input validation en todos los niveles
- **Logging**: Auditoría de eventos de seguridad
- **Rate Limiting**: Protección contra ataques de fuerza bruta

## Testing

- **Tests Unitarios**: Dominio y casos de uso
- **Tests de Integración**: Adaptadores y repositorios
- **Tests de API**: Endpoints REST y GraphQL
- **Cobertura mínima**: 80%

---

*Documentación generada automáticamente desde los modelos C4*
