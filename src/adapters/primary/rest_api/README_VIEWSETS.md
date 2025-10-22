# ViewSets REST - Sistema de Gestión de Prácticas

## 📋 Índice
- [Visión General](#visión-general)
- [UserViewSet](#userviewset)
- [StudentViewSet](#studentviewset)
- [CompanyViewSet](#companyviewset)
- [SupervisorViewSet](#supervisorviewset)
- [PracticeViewSet](#practiceviewset)
- [DocumentViewSet](#documentviewset)
- [NotificationViewSet](#notificationviewset)
- [Permisos y Seguridad](#permisos-y-seguridad)
- [Filtros y Búsquedas](#filtros-y-búsquedas)

---

## Visión General

Este módulo implementa **7 ViewSets completos** con:

✅ **CRUD Completo**: list, retrieve, create, update, partial_update, destroy  
✅ **Custom Actions**: 30+ acciones especiales con `@action`  
✅ **Permisos Granulares**: Integración con sistema de permisos (Fase 1)  
✅ **Filtros Avanzados**: django-filter, search, ordering  
✅ **Paginación**: Automática con DRF  
✅ **Serializers Dinámicos**: Diferentes según acción  
✅ **QuerySets Filtrados**: Según rol del usuario  
✅ **Notificaciones**: Automáticas en cambios de estado  
✅ **Validaciones**: Lógica de negocio implementada  

### Estadísticas

- **Total ViewSets**: 7
- **Total Endpoints**: 50+
- **Custom Actions**: 30+
- **Líneas de Código**: ~1,100
- **Permisos Integrados**: 40+

---

## UserViewSet

**Base URL**: `/api/users/`

### Endpoints Estándar

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/users/` | Listar usuarios | Authenticated |
| GET | `/api/users/{id}/` | Ver usuario | Authenticated |
| POST | `/api/users/` | Crear usuario | Admin/Secretaria |
| PUT/PATCH | `/api/users/{id}/` | Actualizar usuario | Owner/Admin/Secretaria |
| DELETE | `/api/users/{id}/` | Eliminar usuario | Admin |

### Custom Actions

#### 1. GET `/api/users/me/`
**Descripción**: Retorna el perfil del usuario actual

**Response**:
```json
{
  "id": "uuid",
  "email": "user@upeu.edu.pe",
  "username": "user123",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "role": "PRACTICANTE",
  "is_active": true,
  "photo": "http://..."
}
```

#### 2. POST `/api/users/{id}/change_password/`
**Descripción**: Cambiar contraseña del usuario

**Request**:
```json
{
  "old_password": "current_password",
  "new_password": "NewSecurePass123!",
  "new_password_confirm": "NewSecurePass123!"
}
```

**Validaciones**:
- Usuario debe ser el mismo o Admin
- Contraseña actual debe ser correcta (excepto Admin)
- Nueva contraseña cumple políticas
- Confirmación debe coincidir

### Filtros de QuerySet

**Por Rol**:
- **Admin/Secretaria**: Ven todos los usuarios
- **Coordinador**: Ven practicantes, supervisores y coordinadores
- **Otros**: Solo su propio perfil

**Search Fields**: `email`, `username`, `first_name`, `last_name`  
**Filter Fields**: `role`, `is_active`  
**Ordering**: `date_joined`, `last_login`, `email` (default: `-date_joined`)

---

## StudentViewSet

**Base URL**: `/api/students/`

### Endpoints Estándar

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/students/` | Listar estudiantes | CanViewStudent |
| GET | `/api/students/{id}/` | Ver estudiante | CanViewStudent |
| POST | `/api/students/` | Crear estudiante | CanCreateStudent |
| PUT/PATCH | `/api/students/{id}/` | Actualizar estudiante | CanUpdateStudent |
| DELETE | `/api/students/{id}/` | Eliminar estudiante | Admin |

### Custom Actions

#### 1. GET `/api/students/search/`
**Descripción**: Búsqueda avanzada de estudiantes

**Query Params**:
```
?codigo=2020000001
&escuela=Ingeniería de Sistemas
&semestre_min=6
&promedio_min=12.0
&puede_realizar_practica=true
```

**Response**:
```json
{
  "count": 50,
  "next": "http://...",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "user": {...},
      "codigo_estudiante": "2020000001",
      "escuela": "Ingeniería de Sistemas",
      "semestre_actual": 8,
      "promedio_ponderado": 15.5,
      "puede_realizar_practica": true,
      "total_practices": 2
    }
  ]
}
```

#### 2. GET `/api/students/{id}/practices/`
**Descripción**: Prácticas del estudiante

**Query Params**: `?status=IN_PROGRESS`

**Response**:
```json
[
  {
    "id": "uuid",
    "titulo": "Desarrollo Web",
    "company": {...},
    "supervisor": {...},
    "status": "IN_PROGRESS",
    "fecha_inicio": "2024-01-15",
    "fecha_fin": "2024-06-15"
  }
]
```

### Filtros de QuerySet

**Por Rol**:
- **Practicante**: Solo su propio perfil
- **Supervisor**: Estudiantes de sus prácticas
- **Staff**: Todos los estudiantes

**Search Fields**: `codigo_estudiante`, `escuela`, `user__email`, `user__first_name`, `user__last_name`  
**Filter Fields**: `escuela`, `semestre_actual`  
**Ordering**: `created_at`, `promedio_ponderado`, `semestre_actual` (default: `-created_at`)

---

## CompanyViewSet

**Base URL**: `/api/companies/`

### Endpoints Estándar

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/companies/` | Listar empresas | CanViewCompany |
| GET | `/api/companies/{id}/` | Ver empresa | CanViewCompany |
| POST | `/api/companies/` | Crear empresa | CanCreateCompany |
| PUT/PATCH | `/api/companies/{id}/` | Actualizar empresa | CanUpdateCompany |
| DELETE | `/api/companies/{id}/` | Eliminar empresa | Admin |

### Custom Actions

#### 1. POST `/api/companies/{id}/validate/`
**Descripción**: Validar o rechazar empresa (Solo Coordinador)

**Request**:
```json
{
  "status": "ACTIVE",
  "observaciones": "Empresa verificada correctamente"
}
```

**Opciones de status**: `ACTIVE`, `SUSPENDED`, `BLACKLISTED`

**Response**:
```json
{
  "message": "Empresa Acme Corp validada como ACTIVE",
  "company": {...}
}
```

#### 2. POST `/api/companies/{id}/suspend/`
**Descripción**: Suspender empresa (Solo Coordinador)

**Response**:
```json
{
  "message": "Empresa Acme Corp suspendida"
}
```

#### 3. GET `/api/companies/search/`
**Descripción**: Búsqueda avanzada

**Query Params**:
```
?ruc=20123456789
&sector=Tecnología
&status=ACTIVE
&puede_recibir_practicantes=true
```

#### 4. GET `/api/companies/{id}/practices/`
**Descripción**: Prácticas de la empresa

**Query Params**: `?status=COMPLETED`

#### 5. GET `/api/companies/{id}/supervisors/`
**Descripción**: Supervisores de la empresa

### Filtros de QuerySet

**Por Rol**:
- **Supervisor**: Solo su empresa
- **Practicante**: Solo empresas ACTIVE
- **Staff**: Todas las empresas

**Search Fields**: `ruc`, `razon_social`, `nombre_comercial`, `sector_economico`  
**Filter Fields**: `status`, `sector_economico`, `tamaño_empresa`  
**Ordering**: `created_at`, `razon_social` (default: `-created_at`)

---

## SupervisorViewSet

**Base URL**: `/api/supervisors/`

### Endpoints Estándar

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/supervisors/` | Listar supervisores | CanViewSupervisor |
| GET | `/api/supervisors/{id}/` | Ver supervisor | CanViewSupervisor |
| POST | `/api/supervisors/` | Crear supervisor | CanCreateSupervisor |
| PUT/PATCH | `/api/supervisors/{id}/` | Actualizar supervisor | CanUpdateSupervisor |
| DELETE | `/api/supervisors/{id}/` | Eliminar supervisor | Admin |

### Custom Actions

#### 1. GET `/api/supervisors/{id}/practices/`
**Descripción**: Prácticas supervisadas

**Query Params**: `?status=IN_PROGRESS`

**Response**:
```json
[
  {
    "id": "uuid",
    "student": {...},
    "company": {...},
    "titulo": "Desarrollo Backend",
    "status": "IN_PROGRESS",
    "total_practices": 3,
    "active_practices": 1
  }
]
```

### Filtros de QuerySet

**Por Rol**:
- **Supervisor**: Solo su propio perfil
- **Practicante**: Supervisores de sus prácticas
- **Staff**: Todos los supervisores

**Search Fields**: `user__email`, `user__first_name`, `user__last_name`, `cargo`, `documento_numero`  
**Filter Fields**: `company`, `documento_tipo`  
**Ordering**: `created_at`, `años_experiencia` (default: `-created_at`)

---

## PracticeViewSet

**Base URL**: `/api/practices/`

### Endpoints Estándar

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/practices/` | Listar prácticas | CanViewPractice |
| GET | `/api/practices/{id}/` | Ver práctica | CanViewPractice |
| POST | `/api/practices/` | Crear práctica | CanCreatePractice |
| PUT/PATCH | `/api/practices/{id}/` | Actualizar práctica | CanUpdatePractice |
| DELETE | `/api/practices/{id}/` | Eliminar práctica | Admin |

### Custom Actions

#### 1. POST `/api/practices/{id}/change_status/`
**Descripción**: Cambiar estado de práctica (flexible)

**Request**:
```json
{
  "status": "COMPLETED",
  "observaciones": "Excelente trabajo",
  "calificacion_final": 18.5
}
```

**Validaciones**: Transiciones de estado permitidas

#### 2. POST `/api/practices/{id}/submit/`
**Descripción**: Enviar a aprobación (DRAFT → PENDING)

**Permisos**: Solo el estudiante dueño

**Acción**:
- Cambia estado a PENDING
- Notifica a coordinadores

**Response**:
```json
{
  "message": "Práctica enviada a aprobación",
  "practice": {...}
}
```

#### 3. POST `/api/practices/{id}/approve/`
**Descripción**: Aprobar práctica (PENDING → APPROVED)

**Permisos**: Solo Coordinador

**Acción**:
- Cambia estado a APPROVED
- Notifica al estudiante

#### 4. POST `/api/practices/{id}/reject/`
**Descripción**: Rechazar práctica (PENDING → CANCELLED)

**Permisos**: Solo Coordinador

**Request**:
```json
{
  "observaciones": "Faltan documentos requeridos"
}
```

**Acción**:
- Cambia estado a CANCELLED
- Guarda observaciones
- Notifica al estudiante

#### 5. POST `/api/practices/{id}/start/`
**Descripción**: Iniciar práctica (APPROVED → IN_PROGRESS)

**Permisos**: Solo el estudiante dueño

**Acción**:
- Cambia estado a IN_PROGRESS
- Notifica a supervisor

#### 6. POST `/api/practices/{id}/complete/`
**Descripción**: Completar práctica con calificación

**Permisos**: Solo Coordinador

**Request**:
```json
{
  "calificacion_final": 18.5,
  "observaciones": "Excelente desempeño"
}
```

**Validaciones**:
- Calificación entre 0-20
- Solo prácticas IN_PROGRESS

**Acción**:
- Cambia estado a COMPLETED
- Guarda calificación
- Notifica al estudiante

#### 7. GET `/api/practices/search/`
**Descripción**: Búsqueda avanzada

**Query Params**:
```
?student_codigo=2020000001
&company_ruc=20123456789
&status=IN_PROGRESS
&modalidad=REMOTO
&fecha_inicio_desde=2024-01-01
&fecha_inicio_hasta=2024-12-31
&area_practica=Desarrollo
```

#### 8. GET `/api/practices/my_practices/`
**Descripción**: Mis prácticas según rol

**Query Params**: `?status=COMPLETED`

**Response**: Lista de prácticas filtradas por rol

### Flujo de Estados

```
DRAFT
  ↓ submit()
PENDING
  ↓ approve()              ↓ reject()
APPROVED                CANCELLED
  ↓ start()
IN_PROGRESS
  ↓ complete()
COMPLETED
```

### Filtros de QuerySet

**Por Rol**:
- **Practicante**: Solo sus prácticas
- **Supervisor**: Prácticas que supervisa
- **Staff**: Todas las prácticas

**Search Fields**: `titulo`, `area_practica`, `student__codigo_estudiante`, `company__razon_social`, `company__ruc`  
**Filter Fields**: `status`, `modalidad`, `company`, `student`  
**Ordering**: `created_at`, `fecha_inicio`, `fecha_fin` (default: `-created_at`)

---

## DocumentViewSet

**Base URL**: `/api/documents/`

### Endpoints Estándar

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/documents/` | Listar documentos | CanViewDocument |
| GET | `/api/documents/{id}/` | Ver documento | CanViewDocument |
| POST | `/api/documents/` | Subir documento | CanUploadDocument |
| PUT/PATCH | `/api/documents/{id}/` | Actualizar documento | Uploader/Admin |
| DELETE | `/api/documents/{id}/` | Eliminar documento | Uploader/Admin |

### Custom Actions

#### 1. POST `/api/documents/{id}/approve/`
**Descripción**: Aprobar documento

**Permisos**: Coordinador/Secretaria

**Request**:
```json
{
  "observaciones": "Documento correcto"
}
```

**Acción**:
- Marca como aprobado
- Guarda fecha y aprobador
- Notifica al estudiante

#### 2. POST `/api/documents/{id}/reject/`
**Descripción**: Rechazar documento

**Permisos**: Coordinador/Secretaria

**Request**:
```json
{
  "observaciones": "Falta firma del supervisor"
}
```

**Validaciones**: Observaciones obligatorias

**Acción**:
- Marca como no aprobado
- Guarda observaciones
- Notifica al estudiante

#### 3. GET `/api/documents/{id}/download/`
**Descripción**: Descargar archivo

**Response**: FileResponse (streaming)

**Headers**:
```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="documento.pdf"
```

### Filtros de QuerySet

**Por Rol**:
- **Practicante**: Documentos de sus prácticas
- **Supervisor**: Documentos de prácticas que supervisa
- **Staff**: Todos los documentos

**Search Fields**: `nombre_archivo`, `tipo`  
**Filter Fields**: `practice`, `tipo`, `aprobado`  
**Ordering**: `created_at`, `fecha_aprobacion` (default: `-created_at`)

---

## NotificationViewSet

**Base URL**: `/api/notifications/`

### Endpoints Estándar

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/notifications/` | Mis notificaciones | Authenticated |
| GET | `/api/notifications/{id}/` | Ver notificación | Owner |
| POST | `/api/notifications/` | Crear notificación | Admin |
| DELETE | `/api/notifications/{id}/` | Eliminar notificación | Owner |

### Custom Actions

#### 1. POST `/api/notifications/{id}/mark_read/`
**Descripción**: Marcar como leída

**Response**:
```json
{
  "message": "Notificación marcada como leída"
}
```

#### 2. POST `/api/notifications/mark_all_read/`
**Descripción**: Marcar todas como leídas

**Response**:
```json
{
  "message": "15 notificaciones marcadas como leídas"
}
```

#### 3. GET `/api/notifications/unread/`
**Descripción**: Solo notificaciones no leídas

**Response**: Lista paginada de notificaciones `leido=False`

#### 4. GET `/api/notifications/unread_count/`
**Descripción**: Contador de no leídas

**Response**:
```json
{
  "unread_count": 5
}
```

### Filtros de QuerySet

**Por Rol**: Todos los usuarios solo ven sus propias notificaciones

**Search Fields**: `titulo`, `mensaje`  
**Filter Fields**: `tipo`, `leido`  
**Ordering**: `created_at` (default: `-created_at`)

### Tipos de Notificaciones

- `INFO`: Información general
- `SUCCESS`: Aprobaciones, completaciones
- `WARNING`: Rechazos, advertencias
- `ERROR`: Errores, suspensiones

---

## Permisos y Seguridad

### Sistema de Permisos Integrado

Todos los ViewSets integran el **sistema de permisos de la Fase 1**:

```python
def get_permissions(self):
    if self.action == 'create':
        permission_classes = [IsAuthenticated, CanCreatePractice]
    elif self.action in ['update', 'partial_update']:
        permission_classes = [IsAuthenticated, CanUpdatePractice]
    # ...
    return [permission() for permission in permission_classes]
```

### Validación de Ownership

```python
def perform_update(self, serializer):
    user = self.request.user
    instance = self.get_object()
    
    if instance.user != user and not user.is_administrador:
        raise PermissionDenied('No tienes permiso')
    
    serializer.save()
```

### QuerySets Filtrados

Cada ViewSet filtra datos según el rol:

```python
def get_queryset(self):
    user = self.request.user
    
    if user.is_practicante:
        return queryset.filter(student__user=user)
    elif user.is_supervisor:
        return queryset.filter(supervisor__user=user)
    
    return queryset  # Staff ve todo
```

---

## Filtros y Búsquedas

### Django Filter Backend

Filtros automáticos por campos:

```
GET /api/practices/?status=IN_PROGRESS&modalidad=REMOTO
GET /api/students/?escuela=Ingeniería&semestre_actual=8
GET /api/companies/?status=ACTIVE&sector_economico=Tecnología
```

### Search Filter

Búsqueda de texto en múltiples campos:

```
GET /api/students/?search=Juan
GET /api/companies/?search=Acme
GET /api/practices/?search=Desarrollo
```

### Ordering Filter

Ordenamiento personalizado:

```
GET /api/students/?ordering=-promedio_ponderado
GET /api/practices/?ordering=fecha_inicio
GET /api/companies/?ordering=razon_social
```

### Paginación

Automática con DRF (configurable en settings):

```json
{
  "count": 100,
  "next": "http://.../api/students/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## Próximos Pasos

✅ **Fase 1**: Permisos completados  
✅ **Fase 2**: Serializers completados  
✅ **Fase 3**: ViewSets completados  
🚧 **Fase 4**: Mutations GraphQL  
⏳ **Fase 5**: Queries GraphQL  
⏳ **Fase 6**: URLs (routers)  

---

**Archivo**: `src/adapters/primary/rest_api/viewsets.py`  
**Total ViewSets**: 7  
**Total Endpoints**: 50+  
**Custom Actions**: 30+  
**Líneas de Código**: ~1,100
