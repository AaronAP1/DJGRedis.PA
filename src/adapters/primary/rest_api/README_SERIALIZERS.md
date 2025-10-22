# Serializers REST - Sistema de Gestión de Prácticas

## 📋 Índice
- [Visión General](#visión-general)
- [Usuarios (User)](#usuarios-user)
- [Estudiantes (Student)](#estudiantes-student)
- [Empresas (Company)](#empresas-company)
- [Supervisores (Supervisor)](#supervisores-supervisor)
- [Prácticas (Practice)](#prácticas-practice)
- [Documentos (Document)](#documentos-document)
- [Notificaciones (Notification)](#notificaciones-notification)
- [Serializers de Búsqueda](#serializers-de-búsqueda)
- [Validaciones Implementadas](#validaciones-implementadas)

---

## Visión General

Este módulo contiene **50+ serializers** para todas las entidades del sistema, organizados en categorías:

### Categorías de Serializers

Para cada entidad principal, existen:

1. **ListSerializer**: Vista resumida para listados (campos esenciales)
2. **DetailSerializer**: Vista completa con relaciones anidadas
3. **CreateSerializer**: Creación con validaciones completas
4. **UpdateSerializer**: Actualización con validaciones
5. **Serializers Especiales**: Para acciones específicas (aprobar, cambiar estado, etc.)

### Características Generales

✅ **Validaciones de Negocio**: Todas las reglas de negocio implementadas  
✅ **Campos Computados**: `SerializerMethodField` para cálculos  
✅ **Relaciones Anidadas**: Serializers nested para relaciones  
✅ **Seguridad**: Campos sensibles protegidos (`write_only`, `read_only`)  
✅ **Mensajes Descriptivos**: Errores claros y específicos  

---

## Usuarios (User)

### 1. UserListSerializer
**Uso**: Listados, búsquedas, relaciones anidadas

```python
{
    "id": "uuid",
    "email": "string",
    "username": "string",
    "first_name": "string",
    "last_name": "string",
    "full_name": "string",
    "role": "PRACTICANTE|SUPERVISOR|COORDINADOR|SECRETARIA|ADMINISTRADOR",
    "is_active": "boolean",
    "date_joined": "datetime",
    "last_login": "datetime"
}
```

### 2. UserDetailSerializer
**Uso**: Vista detallada de perfil

**Campos Adicionales**:
- `short_name`: Primer nombre
- `photo`: URL de foto de perfil
- `is_practicante`, `is_supervisor`, etc.: Booleanos de rol
- Timestamps de auditoría

### 3. UserCreateSerializer
**Uso**: Registro de nuevos usuarios

**Campos Requeridos**:
```python
{
    "email": "string",
    "username": "string", 
    "first_name": "string",
    "last_name": "string",
    "password": "string",
    "role": "string"
}
```

**Validaciones**:
- ✅ Email único en el sistema
- ✅ Dominio @upeu.edu.pe obligatorio para PRACTICANTE
- ✅ Password cumple políticas de Django
- ✅ Rol válido del enum

### 4. UserUpdateSerializer
**Uso**: Actualización de perfil

**Campos Editables**: first_name, last_name, photo

### 5. ChangePasswordSerializer
**Uso**: Cambio de contraseña

```python
{
    "old_password": "string",
    "new_password": "string",
    "new_password_confirm": "string"
}
```

**Validaciones**:
- ✅ Contraseña actual correcta
- ✅ Nueva contraseña cumple políticas
- ✅ Confirmación coincide

---

## Estudiantes (Student)

### 1. StudentListSerializer
**Campos Computados**:
- `total_practices`: Cantidad de prácticas
- `puede_realizar_practica`: Boolean (semestre >= 6 AND promedio >= 12.0)

### 2. StudentDetailSerializer
**Campos Adicionales**:
- `active_practices`: Prácticas en progreso
- `completed_practices`: Prácticas completadas

### 3. StudentCreateSerializer

**Campos Requeridos**:
```python
{
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "password": "string",
    "codigo_estudiante": "string",  # YYYY + 6 dígitos
    "escuela": "string",
    "semestre_actual": "integer",
    "promedio_ponderado": "decimal"
}
```

**Validaciones Especiales**:
- ✅ Código formato YYYYNNNNNN (2020000001)
- ✅ Email @upeu.edu.pe obligatorio
- ✅ Semestre entre 1-12
- ✅ Promedio entre 0-20
- ✅ Usuario se crea automáticamente con rol PRACTICANTE

**Lógica de Creación**:
1. Crear User con rol PRACTICANTE
2. Crear Student vinculado al User
3. Transacción atómica (rollback si falla alguno)

### 4. StudentUpdateSerializer
**Campos Editables**: escuela, semestre_actual, promedio_ponderado

---

## Empresas (Company)

### 1. CompanyListSerializer
**Campos Computados**:
- `total_practices`: Cantidad de prácticas recibidas
- `puede_recibir_practicantes`: Boolean (status == ACTIVE)

### 2. CompanyDetailSerializer
**Campos Adicionales**:
- `active_practices`: Prácticas activas
- `total_supervisors`: Supervisores registrados

### 3. CompanyCreateSerializer

**Campos Requeridos**:
```python
{
    "ruc": "string",  # 11 dígitos
    "razon_social": "string",
    "direccion": "string",
    "telefono": "string",
    "email": "string",
    "sector_economico": "string",
    "tamaño_empresa": "MICRO|PEQUEÑA|MEDIANA|GRANDE"
}
```

**Validaciones Especiales**:
- ✅ RUC 11 dígitos numéricos únicos
- ✅ Email único
- ✅ Se crea con `status='PENDING_VALIDATION'` automáticamente

### 4. CompanyUpdateSerializer
**Campos Editables**: Todos excepto RUC

### 5. CompanyValidateSerializer
**Uso**: Coordinadores validan empresas

```python
{
    "status": "ACTIVE|SUSPENDED|BLACKLISTED",
    "observaciones": "string"  # opcional
}
```

---

## Supervisores (Supervisor)

### 1. SupervisorListSerializer
**Campos Computados**:
- `total_practices`: Prácticas supervisadas

### 2. SupervisorDetailSerializer
**Campos Adicionales**:
- `active_practices`: Prácticas activas supervisando
- `completed_practices`: Prácticas completadas

### 3. SupervisorCreateSerializer

**Campos Requeridos**:
```python
{
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "password": "string",
    "company_id": "uuid",
    "documento_tipo": "DNI|CE|PASAPORTE",
    "documento_numero": "string",
    "cargo": "string",
    "telefono": "string",
    "años_experiencia": "integer"  # opcional
}
```

**Validaciones Especiales**:
- ✅ Empresa debe existir y estar ACTIVE o PENDING_VALIDATION
- ✅ Años experiencia: 0-60
- ✅ Usuario se crea automáticamente con rol SUPERVISOR

**Lógica de Creación**:
1. Crear User con rol SUPERVISOR
2. Vincular a Company
3. Crear Supervisor

### 4. SupervisorUpdateSerializer
**Campos Editables**: documento_tipo, documento_numero, cargo, telefono, años_experiencia

---

## Prácticas (Practice)

### 1. PracticeListSerializer
**Campos Computados**:
- `duracion_dias`: Días entre inicio y fin (property del modelo)
- `esta_activa`: Boolean (property del modelo)

### 2. PracticeDetailSerializer
**Campos Adicionales**:
- `total_documents`: Documentos subidos
- `approved_documents`: Documentos aprobados
- `progreso_porcentual`: % avance basado en fechas (0-100)

**Cálculo de Progreso**:
```python
if ahora < inicio: return 0.0
if ahora >= fin: return 100.0
return (dias_transcurridos / dias_totales) * 100
```

### 3. PracticeCreateSerializer

**Campos Requeridos**:
```python
{
    "student_id": "uuid",
    "company_id": "uuid",
    "supervisor_id": "uuid",  # opcional
    "titulo": "string",
    "descripcion": "text",
    "objetivos": "text",
    "fecha_inicio": "date",
    "fecha_fin": "date",
    "horas_totales": "integer",  # mínimo 480
    "modalidad": "PRESENCIAL|REMOTO|HIBRIDO",
    "area_practica": "string"
}
```

**Validaciones Especiales**:
- ✅ Estudiante cumple requisitos (semestre >= 6, promedio >= 12.0)
- ✅ Empresa puede recibir practicantes (status == ACTIVE)
- ✅ Horas totales >= 480
- ✅ Fecha fin > fecha inicio
- ✅ Duración mínima 3 meses (90 días)
- ✅ Se crea con `status='DRAFT'`

### 4. PracticeUpdateSerializer
**Campos Editables**: titulo, descripcion, objetivos, fechas, horas, modalidad, area, supervisor, observaciones

**Validaciones**: Mantiene validación de fechas y horas

### 5. PracticeStatusSerializer
**Uso**: Cambiar estado de práctica

```python
{
    "status": "DRAFT|PENDING|APPROVED|IN_PROGRESS|COMPLETED|CANCELLED|SUSPENDED",
    "observaciones": "string",
    "calificacion_final": "decimal"  # 0-20, requerido si COMPLETED
}
```

**Transiciones Permitidas**:
```
DRAFT → PENDING
PENDING → APPROVED | CANCELLED
APPROVED → IN_PROGRESS | CANCELLED
IN_PROGRESS → COMPLETED | SUSPENDED | CANCELLED
SUSPENDED → IN_PROGRESS | CANCELLED
COMPLETED → (ninguna)
CANCELLED → (ninguna)
```

**Validaciones**:
- ✅ Transición válida según estado actual
- ✅ Si se completa, requiere calificación 0-20

---

## Documentos (Document)

### 1. DocumentListSerializer
**Campos Computados**:
- `file_size_mb`: Tamaño en MB con 2 decimales

### 2. DocumentDetailSerializer
**Campos Adicionales**:
- `file_extension`: Extensión del archivo (.pdf, .doc, etc.)
- `download_url`: URL absoluta para descarga

### 3. DocumentCreateSerializer

**Campos Requeridos**:
```python
{
    "practice_id": "uuid",
    "tipo": "PLAN_TRABAJO|INFORME_PARCIAL|INFORME_FINAL|CERTIFICADO|OTRO",
    "archivo": "file",
    "nombre_archivo": "string"  # opcional, usa nombre del archivo si no se proporciona
}
```

**Validaciones de Archivo**:
- ✅ Tamaño máximo: 10 MB
- ✅ Extensiones permitidas: .pdf, .doc, .docx, .jpg, .jpeg, .png, .zip
- ✅ Se asigna `uploaded_by` automáticamente
- ✅ Se crea con `aprobado=False`

### 4. DocumentUpdateSerializer
**Campos Editables**: tipo, archivo (opcional), nombre_archivo, observaciones

### 5. DocumentApproveSerializer
**Uso**: Coordinadores aprueban/rechazan documentos

```python
{
    "aprobado": "boolean",
    "observaciones": "string"  # requerido si aprobado=false
}
```

**Validaciones**:
- ✅ Si se rechaza, debe tener observaciones explicando el motivo

---

## Notificaciones (Notification)

### 1. NotificationListSerializer
**Campos Computados**:
- `time_since`: Tiempo transcurrido (ej: "hace 2 horas")

### 2. NotificationDetailSerializer
**Campos Adicionales**:
- `related_practice`: Práctica relacionada (nested)
- `related_document`: Documento relacionado (nested)
- `metadata`: JSONField con datos adicionales

### 3. NotificationCreateSerializer

**Campos Requeridos**:
```python
{
    "user_id": "uuid",
    "tipo": "INFO|SUCCESS|WARNING|ERROR",
    "titulo": "string",
    "mensaje": "text",
    "practice_id": "uuid",  # opcional
    "document_id": "uuid",  # opcional
    "metadata": "json"  # opcional
}
```

**Lógica**:
- Se crea con `leido=False` automáticamente
- Puede vincular a práctica y/o documento

### 4. NotificationMarkAsReadSerializer
**Uso**: Marcar múltiples notificaciones como leídas

```python
{
    "notification_ids": ["uuid1", "uuid2", "uuid3"]
}
```

**Validaciones**:
- ✅ Todas las notificaciones existen
- ✅ Todas pertenecen al usuario actual

---

## Serializers de Búsqueda

### PracticeSearchSerializer
**Campos de Filtro**:
```python
{
    "student_codigo": "string",
    "company_ruc": "string",
    "status": "enum",
    "modalidad": "enum",
    "fecha_inicio_desde": "date",
    "fecha_inicio_hasta": "date",
    "fecha_fin_desde": "date",
    "fecha_fin_hasta": "date",
    "area_practica": "string"
}
```

### StudentSearchSerializer
```python
{
    "codigo": "string",
    "escuela": "string",
    "semestre_min": "integer",
    "promedio_min": "decimal",
    "puede_realizar_practica": "boolean"
}
```

### CompanySearchSerializer
```python
{
    "ruc": "string",
    "sector": "string",
    "status": "enum",
    "puede_recibir_practicantes": "boolean"
}
```

### DashboardStatsSerializer
**Uso**: Estadísticas del dashboard

```python
{
    "total_students": "integer",
    "total_companies": "integer",
    "total_practices": "integer",
    "active_practices": "integer",
    "completed_practices": "integer",
    "pending_documents": "integer",
    "unread_notifications": "integer",
    "practices_by_status": {"DRAFT": 5, "APPROVED": 10, ...},
    "practices_by_modalidad": {"PRESENCIAL": 20, "REMOTO": 15, ...},
    "top_companies": ["company1", "company2", ...],
    "recent_practices": [...]
}
```

---

## Validaciones Implementadas

### 📧 Validaciones de Email
- **Unicidad**: No puede existir duplicado
- **Dominio**: @upeu.edu.pe obligatorio para PRACTICANTE
- **Formato**: Django valida formato estándar

### 🔑 Validaciones de Password
- **Longitud mínima**: 8 caracteres (configurable)
- **Complejidad**: Usa `validate_password` de Django
- **Confirmación**: Debe coincidir en cambio de password

### 📄 Validaciones de Archivos
- **Tamaño**: Máximo 10 MB
- **Extensiones**: Solo .pdf, .doc, .docx, .jpg, .jpeg, .png, .zip
- **Seguridad**: Validación de content-type

### 🏢 Validaciones de Empresa
- **RUC**: 11 dígitos numéricos únicos
- **Estado**: Solo ACTIVE puede recibir practicantes
- **Email**: Único en el sistema

### 👨‍🎓 Validaciones de Estudiante
- **Código**: Formato YYYYNNNNNN (2020000001)
- **Semestre**: Entre 1-12
- **Promedio**: Entre 0-20 (decimal con 2 decimales)
- **Elegibilidad**: semestre >= 6 AND promedio >= 12.0

### 📝 Validaciones de Práctica
- **Horas**: Mínimo 480 horas
- **Duración**: Mínimo 3 meses (90 días)
- **Fechas**: Fin debe ser posterior a inicio
- **Elegibilidad**: Estudiante debe cumplir requisitos
- **Estado**: Solo ACTIVE puede recibir prácticas
- **Calificación**: 0-20 al completar

### 🔄 Validaciones de Estado
- **Transiciones**: Solo cambios permitidos según diagrama de estados
- **Completar**: Requiere calificación
- **Rechazar Documento**: Requiere observaciones

### 📊 Validaciones de Datos
- **Años Experiencia**: 0-60
- **Calificación**: 0-20 con 2 decimales
- **Teléfonos**: Formato numérico
- **Fechas**: No futuras donde no aplique

---

## Uso en ViewSets

Los serializers están diseñados para usarse con `get_serializer_class()` en ViewSets:

```python
class PracticeViewSet(ModelViewSet):
    def get_serializer_class(self):
        if self.action == 'list':
            return PracticeListSerializer
        elif self.action == 'retrieve':
            return PracticeDetailSerializer
        elif self.action == 'create':
            return PracticeCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return PracticeUpdateSerializer
        elif self.action == 'change_status':
            return PracticeStatusSerializer
        return PracticeDetailSerializer
```

---

## Próximos Pasos

✅ **Fase 2 Completada**: Serializers con validaciones  
🚧 **Fase 3**: ViewSets REST con CRUD y custom actions  
⏳ **Fase 4**: Mutations GraphQL  
⏳ **Fase 5**: Queries GraphQL avanzadas  

---

**Archivo**: `src/adapters/primary/rest_api/serializers.py`  
**Total de Serializers**: 50+  
**Líneas de Código**: ~1,400  
**Cobertura**: 7 entidades principales + auxiliares
