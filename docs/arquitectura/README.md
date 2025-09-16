# Documentación de Diagramas de Arquitectura

Esta carpeta contiene los principales diagramas para documentar la arquitectura y el diseño del sistema de gestión de prácticas profesionales de la Universidad Peruana Unión.

## 📋 Índice de Diagramas

### 1. Diagramas C4 (Context, Container, Component)

#### 1.1 Contexto y Contenedores Robusto
**Archivo:** `C4_Contexto_Contenedores_Robusto.puml`

Representa los actores principales del sistema (Practicante, Supervisor, Coordinador EP, Secretaria, Administrador, SuperAdmin, Empresa) y los contenedores tecnológicos principales:
- Django 5.0 + DRF (API REST y GraphQL)
- PostgreSQL (Base de datos principal)
- Redis (Cache y sesiones)
- MongoDB (Documentos y archivos)
- Celery (Procesamiento asíncrono)
- Servicios externos (SUNAT, RENIEC, SUNEDU)

Incluye también la gestión de CVs, oportunidades laborales y validaciones.

#### 1.2 Diagrama de Componentes
**Archivo:** `C4_Componentes.puml`

Detalla los componentes internos de la aplicación Django según la arquitectura hexagonal:
- **Controllers:** Auth, Práctica, Empresa, Oportunidad, Documento, CV
- **Use Cases:** Casos de uso por dominio
- **Domain:** Entidades y Value Objects
- **Repositories:** Persistencia de datos
- **Services:** Validación, archivos, notificaciones, logging

### 2. Diagrama de Entidades y Estados
**Archivo:** `Entidades_Estados_Robusto.puml`

Muestra el modelo de datos completo con todas las entidades principales:
- **Gestión de usuarios:** upeu_usuario, upeu_rol, perfiles específicos
- **Gestión académica:** upeu_escuela, upeu_rama, upeu_perfil_practicante
- **Gestión empresarial:** upeu_empresa, upeu_perfil_supervisor
- **Gestión de prácticas:** upeu_practica, upeu_documento_practica
- **Oportunidades laborales:** upeu_oportunidad_laboral, upeu_postulacion_oportunidad

Incluye el diagrama de estados para el ciclo de vida de una práctica:
`BORRADOR → PENDIENTE → APROBADO → EN_PROGRESO → COMPLETADO`

### 3. Modelo de Base de Datos Completo
**Archivo:** `Modelo_BD_Completo.puml`

Diagrama detallado con **más de 20 tablas** que incluye:

#### 3.1 Configuración y Gestión
- `upeu_escuela`: Escuelas profesionales
- `upeu_configuracion`: Parámetros del sistema
- `upeu_rama`: Ramas profesionales por escuela

#### 3.2 Usuarios y Roles
- `upeu_usuario`: Usuarios base del sistema
- `upeu_rol`: Roles con permisos
- Perfiles específicos: `upeu_perfil_practicante`, `upeu_perfil_supervisor`, etc.

#### 3.3 Gestión de Prácticas
- `upeu_practica`: Prácticas profesionales
- `upeu_historial_estado_practica`: Seguimiento de cambios de estado
- `upeu_documento_practica`: Documentos asociados
- `upeu_validacion`: Validaciones y aprobaciones

#### 3.4 Oportunidades Laborales
- `upeu_oportunidad_laboral`: Ofertas de trabajo
- `upeu_postulacion_oportunidad`: Postulaciones de practicantes

#### 3.5 Evaluación y Reportes
- `upeu_reporte_practica`: Reportes de progreso
- `upeu_evaluacion_practica`: Evaluaciones de desempeño

#### 3.6 Comunicación y Auditoría
- `upeu_notificacion`: Sistema de notificaciones
- `upeu_mensaje`: Comunicación interna
- `upeu_log_auditoria`: Trazabilidad completa
- `upeu_sesion_usuario`: Gestión de sesiones

### 4. Diagrama de Clases
**Archivo:** `Diagrama_Clases_Robusto.puml`

Presenta la arquitectura hexagonal completa:

#### 4.1 Domain Layer
- **Entidades:** Usuario, Práctica, Empresa, OportunidadLaboral, etc.
- **Value Objects:** Email, DNI, RUC, CodigoEstudiante
- **Enums:** RolEnum, EstadoPracticaEnum, EstadoDocumentoEnum

#### 4.2 Application Layer
- **Use Cases:** CrearPracticaUseCase, ValidarDocumentoUseCase, PostularOportunidadUseCase, SubirCVUseCase
- **DTOs:** Request/Response objects

#### 4.3 Ports (Interfaces)
- **Repository Ports:** PracticaRepositoryPort, EmpresaRepositoryPort
- **Service Ports:** FileServicePort, NotificationServicePort, ValidationServicePort

#### 4.4 Adapters (Implementaciones)
- **Repository Adapters:** DjangoPracticaRepository, DjangoEmpresaRepository
- **Service Adapters:** S3FileService, EmailNotificationService, SunatValidationService
- **API Controllers:** RestApiController, GraphQLApiController

### 5. Diagramas de Secuencia
**Archivo:** `Secuencias_Casos_Uso.puml`

Documenta los flujos principales del sistema:

#### 5.1 Registro de Práctica
Flujo completo desde el practicante hasta la persistencia, incluyendo validaciones de empresa y notificaciones al coordinador.

#### 5.2 Subida de CV
Proceso de subida de CV con almacenamiento en S3 y actualización del perfil del practicante.

#### 5.3 Postulación a Oportunidad Laboral
Flujo de postulación con validaciones de vigencia y notificaciones a la empresa.

#### 5.4 Validación de Documento
Proceso de validación por parte de la secretaria con verificación de permisos y notificaciones.

#### 5.5 Aprobación de Práctica
Flujo de aprobación por el coordinador con cambio de estado y notificaciones a stakeholders.

## 🛠️ Herramientas para Visualización

Para visualizar los diagramas PlantUML:

### 1. VS Code (Recomendado)
```bash
# Instalar extensión PlantUML
ext install plantuml
```

### 2. Online
- [PlantUML Online Server](http://plantuml.com/plantuml/uml/)
- [PlantText](https://www.planttext.com/)

### 3. Local
```bash
# Instalar PlantUML
npm install -g plantuml
# Generar imagen
plantuml diagrama.puml
```

## 🔄 Actualizaciones

Los diagramas deben actualizarse cuando:
- Se agreguen nuevas funcionalidades
- Se modifique la arquitectura
- Se cambien las relaciones entre entidades
- Se agreguen nuevos roles o permisos

## 📁 Archivos Disponibles

| Archivo | Descripción | Tipo |
|---------|-------------|------|
| `C4_Contexto_Contenedores_Robusto.puml` | Contexto y contenedores C4 | Arquitectura |
| `C4_Componentes.puml` | Componentes internos C4 | Arquitectura |
| `Entidades_Estados_Robusto.puml` | Entidades y estados | Datos |
| `Modelo_BD_Completo.puml` | Modelo completo de BD | Datos |
| `Diagrama_Clases_Robusto.puml` | Clases y arquitectura hexagonal | Código |
| `Secuencias_Casos_Uso.puml` | Secuencias de casos de uso | Comportamiento |
| `C4_Contexto_Contenedores.puml` | Versión original (legacy) | Legacy |
| `Diagrama_Clases.puml` | Versión original (legacy) | Legacy |
| `Entidades_Estados.puml` | Versión original (legacy) | Legacy |
| `Secuencia_Registro_Practica.puml` | Versión original (legacy) | Legacy |

## 🎯 Características del Sistema Documentadas

- ✅ Gestión multi-escuela profesional
- ✅ 6 roles de usuario con permisos específicos
- ✅ Gestión completa de prácticas profesionales
- ✅ Sistema de subida y gestión de CVs
- ✅ Oportunidades laborales y postulaciones
- ✅ Validación de documentos por roles
- ✅ Auditoría completa y trazabilidad
- ✅ Notificaciones y comunicación interna
- ✅ Integración con sistemas externos (SUNAT, RENIEC, SUNEDU)
- ✅ Arquitectura hexagonal con separación clara de responsabilidades
- ✅ Más de 20 tablas para gestión robusta

¿Necesitas agregar más diagramas o detalles específicos?
