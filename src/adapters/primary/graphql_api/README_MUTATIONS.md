# GraphQL Mutations - Sistema de Gestión de Prácticas Profesionales

## Descripción General

Este documento describe todas las mutations GraphQL disponibles en el sistema. Las mutations están organizadas por entidad y incluyen validaciones, permisos y notificaciones automáticas.

**Archivo**: `src/adapters/primary/graphql_api/mutations_complete.py`

**Total de Mutations**: 30+

---

## Características Principales

### 🔒 Sistema de Permisos
- Decorators de Fase 1: `@login_required`, `@staff_required`, `@administrador_required`, `@coordinador_required`
- Permission helpers: `can_create_*()`, `can_update_*()`, etc.
- Validación de roles y ownership

### ✅ Validaciones
- Email domain para estudiantes (@upeu.edu.pe)
- Formato de código estudiantil (YYYYNNNNNN)
- Rangos válidos (semestre 1-12, promedio 0-20, horas 480-2000)
- RUC de 11 dígitos
- Transiciones de estado válidas

### 🔔 Notificaciones Automáticas
- Generación automática en cambios de estado
- Notificaciones a roles relevantes (coordinadores, estudiantes, supervisores)
- Helper function `create_notification()`

### 🔄 Máquina de Estados
- Validación de transiciones permitidas
- Estado inicial y estados finales definidos
- Helper function `validate_practice_status_transition()`

---

## 1. USER MUTATIONS

### CreateUserMutation
Crear nuevo usuario (Staff required)

```graphql
mutation {
  createUser(
    email: "usuario@upeu.edu.pe"
    username: "usuario2024"
    firstName: "Juan"
    lastName: "Pérez"
    password: "Password123!"
    role: "PRACTICANTE"
    dni: "12345678"
    telefono: "987654321"
  ) {
    success
    message
    user {
      id
      email
      role
      fullName
    }
  }
}
```

**Permisos**: `@staff_required` (COORDINADOR, SECRETARIA, ADMINISTRADOR)

**Validaciones**:
- Username único
- Email único
- Role válido: PRACTICANTE, SUPERVISOR, COORDINADOR, SECRETARIA, ADMINISTRADOR
- DNI de 8 dígitos
- Teléfono de 9 dígitos

---

### UpdateUserMutation
Actualizar usuario existente

```graphql
mutation {
  updateUser(
    userId: "1"
    firstName: "Juan Carlos"
    telefono: "999888777"
    isActive: true
  ) {
    success
    message
    user {
      id
      firstName
      telefono
      isActive
    }
  }
}
```

**Permisos**: 
- Staff puede actualizar cualquier usuario
- Usuario normal solo puede actualizarse a sí mismo

**Campos actualizables**: firstName, lastName, telefono, isActive (solo staff)

---

### DeleteUserMutation
Eliminar usuario (Admin only)

```graphql
mutation {
  deleteUser(userId: "5") {
    success
    message
  }
}
```

**Permisos**: `@administrador_required`

**Restricciones**: No puede eliminar su propia cuenta

---

### ChangePasswordMutation
Cambiar contraseña

```graphql
mutation {
  changePassword(
    currentPassword: "OldPassword123!"
    newPassword: "NewPassword456!"
  ) {
    success
    message
  }
}
```

**Permisos**: Usuario autenticado

**Validaciones**:
- Contraseña actual correcta
- Nueva contraseña diferente a la actual
- Nueva contraseña cumple requisitos de complejidad

---

## 2. STUDENT MUTATIONS

### CreateStudentMutation
Crear nuevo estudiante (crea User + Student)

```graphql
mutation {
  createStudent(
    email: "2024012345@upeu.edu.pe"
    firstName: "María"
    lastName: "García"
    password: "Student123!"
    codigo: "2024012345"
    semestre: 6
    escuelaProfesional: "Ingeniería de Sistemas"
    promedio: 15.5
  ) {
    success
    message
    student {
      id
      codigo
      semestre
      promedio
      user {
        fullName
        email
      }
    }
  }
}
```

**Permisos**: `can_create_student()` - COORDINADOR, SECRETARIA, ADMINISTRADOR

**Validaciones**:
- Email formato `*@upeu.edu.pe`
- Código formato `YYYYNNNNNN` (año + 6 dígitos)
- Semestre entre 1 y 12
- Promedio entre 0.0 y 20.0
- Código único

---

### UpdateStudentMutation
Actualizar estudiante existente

```graphql
mutation {
  updateStudent(
    studentId: "1"
    semestre: 7
    promedio: 16.2
    escuelaProfesional: "Ingeniería de Sistemas"
  ) {
    success
    message
    student {
      id
      semestre
      promedio
    }
  }
}
```

**Permisos**: `can_update_student()` - Staff o el mismo estudiante

**Campos actualizables**: semestre, escuelaProfesional, promedio

---

### DeleteStudentMutation
Eliminar estudiante (Admin only)

```graphql
mutation {
  deleteStudent(studentId: "3") {
    success
    message
  }
}
```

**Permisos**: `@administrador_required`

---

## 3. COMPANY MUTATIONS

### CreateCompanyMutation
Crear nueva empresa

```graphql
mutation {
  createCompany(
    ruc: "20123456789"
    razonSocial: "Tech Solutions SAC"
    nombreComercial: "TechSol"
    direccion: "Av. Arequipa 1234, Lima"
    telefono: "014567890"
    email: "contacto@techsol.com"
    sectorEconomico: "Tecnología"
    tamañoEmpresa: "MEDIANA"
  ) {
    success
    message
    company {
      id
      razonSocial
      ruc
      status
    }
  }
}
```

**Permisos**: `can_create_company()` - Staff

**Validaciones**:
- RUC de 11 dígitos numéricos
- RUC único
- Tamaño válido: MICRO, PEQUEÑA, MEDIANA, GRANDE

**Estado inicial**: `PENDING_VALIDATION`

**Notificaciones**: Notifica a coordinadores

---

### UpdateCompanyMutation
Actualizar empresa

```graphql
mutation {
  updateCompany(
    companyId: "1"
    telefono: "014567899"
    email: "nuevo@techsol.com"
  ) {
    success
    message
    company {
      id
      telefono
      email
    }
  }
}
```

**Permisos**: `can_update_company()` - Staff o usuario asociado a la empresa

---

### ValidateCompanyMutation
Validar o cambiar estado de empresa (Coordinador only)

```graphql
mutation {
  validateCompany(
    companyId: "1"
    status: "ACTIVE"
    observaciones: "Empresa validada correctamente"
  ) {
    success
    message
    company {
      id
      razonSocial
      status
    }
  }
}
```

**Permisos**: `@coordinador_required`

**Estados válidos**: ACTIVE, SUSPENDED, BLACKLISTED

---

### DeleteCompanyMutation
Eliminar empresa (Admin only)

```graphql
mutation {
  deleteCompany(companyId: "2") {
    success
    message
  }
}
```

**Permisos**: `@administrador_required`

---

## 4. SUPERVISOR MUTATIONS

### CreateSupervisorMutation
Crear nuevo supervisor (crea User + Supervisor)

```graphql
mutation {
  createSupervisor(
    email: "supervisor@empresa.com"
    firstName: "Carlos"
    lastName: "Rodríguez"
    password: "Supervisor123!"
    companyId: "1"
    documentoTipo: "DNI"
    documentoNumero: "87654321"
    cargo: "Jefe de TI"
    telefono: "987654321"
    añosExperiencia: 5
  ) {
    success
    message
    supervisor {
      id
      cargo
      añosExperiencia
      user {
        fullName
        email
      }
      company {
        razonSocial
      }
    }
  }
}
```

**Permisos**: `can_create_supervisor()` - Staff

**Validaciones**:
- Empresa debe existir y estar activa o pending
- Años experiencia entre 0 y 60

---

### UpdateSupervisorMutation
Actualizar supervisor

```graphql
mutation {
  updateSupervisor(
    supervisorId: "1"
    cargo: "Gerente de TI"
    añosExperiencia: 7
  ) {
    success
    message
    supervisor {
      id
      cargo
      añosExperiencia
    }
  }
}
```

**Permisos**: `can_update_supervisor()` - Staff o el mismo supervisor

---

### DeleteSupervisorMutation
Eliminar supervisor (Admin only)

```graphql
mutation {
  deleteSupervisor(supervisorId: "2") {
    success
    message
  }
}
```

**Permisos**: `@administrador_required`

---

## 5. PRACTICE MUTATIONS

### CreatePracticeMutation
Crear nueva práctica

```graphql
mutation {
  createPractice(
    studentId: "1"
    companyId: "1"
    supervisorId: "1"
    tipo: "PREPROFESIONAL"
    area: "Desarrollo de Software"
    fechaInicio: "2024-03-01"
    fechaFin: "2024-08-31"
    horasRequeridas: 640
    descripcionActividades: "Desarrollo de aplicaciones web"
  ) {
    success
    message
    practice {
      id
      tipo
      area
      status
      student {
        user {
          fullName
        }
      }
      company {
        razonSocial
      }
    }
  }
}
```

**Permisos**: `can_create_practice()` - Staff o el propio estudiante

**Validaciones**:
- Estudiante existe
- Empresa activa
- Supervisor pertenece a la empresa
- Tipo: PREPROFESIONAL, PROFESIONAL
- Horas entre 480 y 2000

**Estado inicial**: `DRAFT`

**Notificaciones**: Notifica a coordinadores

---

### UpdatePracticeMutation
Actualizar práctica (solo si está en DRAFT o PENDING)

```graphql
mutation {
  updatePractice(
    practiceId: "1"
    area: "Desarrollo Web Full Stack"
    horasRequeridas: 720
  ) {
    success
    message
    practice {
      id
      area
      horasRequeridas
    }
  }
}
```

**Permisos**: `can_update_practice()` - Staff o el estudiante owner

**Restricciones**: No se puede actualizar si está APPROVED, IN_PROGRESS o COMPLETED

---

### SubmitPracticeMutation
Enviar práctica a revisión (DRAFT → PENDING)

```graphql
mutation {
  submitPractice(practiceId: "1") {
    success
    message
    practice {
      id
      status
    }
  }
}
```

**Permisos**: Solo el estudiante owner

**Transición**: `DRAFT` → `PENDING`

**Notificaciones**: Notifica a coordinadores

---

### ApprovePracticeMutation
Aprobar práctica (PENDING → APPROVED) - Coordinador only

```graphql
mutation {
  approvePractice(
    practiceId: "1"
    observaciones: "Práctica aprobada sin observaciones"
  ) {
    success
    message
    practice {
      id
      status
    }
  }
}
```

**Permisos**: `@coordinador_required`

**Transición**: `PENDING` → `APPROVED`

**Notificaciones**: Notifica al estudiante

---

### RejectPracticeMutation
Rechazar práctica (PENDING → DRAFT) - Coordinador only

```graphql
mutation {
  rejectPractice(
    practiceId: "1"
    observaciones: "Necesita completar información de actividades"
  ) {
    success
    message
    practice {
      id
      status
    }
  }
}
```

**Permisos**: `@coordinador_required`

**Transición**: `PENDING` → `DRAFT`

**Notificaciones**: Notifica al estudiante con observaciones

---

### StartPracticeMutation
Iniciar práctica (APPROVED → IN_PROGRESS)

```graphql
mutation {
  startPractice(practiceId: "1") {
    success
    message
    practice {
      id
      status
    }
  }
}
```

**Permisos**: Coordinador o el estudiante owner

**Transición**: `APPROVED` → `IN_PROGRESS`

**Notificaciones**: Notifica a estudiante y supervisor

---

### CompletePracticeMutation
Completar práctica (IN_PROGRESS → COMPLETED) - Coordinador only

```graphql
mutation {
  completePractice(practiceId: "1") {
    success
    message
    practice {
      id
      status
    }
  }
}
```

**Permisos**: `@coordinador_required`

**Transición**: `IN_PROGRESS` → `COMPLETED`

**Notificaciones**: Notifica al estudiante con felicitaciones

---

### DeletePracticeMutation
Eliminar práctica

```graphql
mutation {
  deletePractice(practiceId: "3") {
    success
    message
  }
}
```

**Permisos**: 
- Admin puede eliminar cualquiera
- Estudiante solo puede eliminar si está en DRAFT

---

## 6. DOCUMENT MUTATIONS

### CreateDocumentMutation
Subir nuevo documento

```graphql
mutation {
  createDocument(
    practiceId: "1"
    tipoDocumento: "INFORME_MENSUAL"
    nombre: "Informe Mes 1"
    archivoUrl: "https://storage.example.com/doc123.pdf"
    observaciones: "Primer informe mensual"
  ) {
    success
    message
    document {
      id
      tipoDocumento
      nombre
      status
    }
  }
}
```

**Permisos**: Solo el estudiante owner de la práctica

**Tipos válidos**: 
- PLAN_TRABAJO
- INFORME_MENSUAL
- INFORME_FINAL
- CERTIFICADO
- CONSTANCIA
- EVALUACION
- OTRO

**Estado inicial**: `PENDING`

**Notificaciones**: Notifica a coordinadores

---

### ApproveDocumentMutation
Aprobar documento (Coordinador only)

```graphql
mutation {
  approveDocument(
    documentId: "1"
    observaciones: "Documento correcto"
  ) {
    success
    message
    document {
      id
      status
    }
  }
}
```

**Permisos**: `@coordinador_required`

**Estado final**: `APPROVED`

**Notificaciones**: Notifica al estudiante

---

### RejectDocumentMutation
Rechazar documento (Coordinador only)

```graphql
mutation {
  rejectDocument(
    documentId: "1"
    observaciones: "Falta firma del supervisor"
  ) {
    success
    message
    document {
      id
      status
    }
  }
}
```

**Permisos**: `@coordinador_required`

**Estado final**: `REJECTED`

**Notificaciones**: Notifica al estudiante con observaciones

---

### DeleteDocumentMutation
Eliminar documento

```graphql
mutation {
  deleteDocument(documentId: "2") {
    success
    message
  }
}
```

**Permisos**:
- Admin puede eliminar cualquiera
- Estudiante solo puede eliminar si está PENDING

---

## 7. NOTIFICATION MUTATIONS

### MarkNotificationAsReadMutation
Marcar notificación como leída

```graphql
mutation {
  markNotificationRead(notificationId: "5") {
    success
    message
    notification {
      id
      leido
    }
  }
}
```

**Permisos**: Solo el usuario owner de la notificación

---

### MarkAllNotificationsReadMutation
Marcar todas las notificaciones como leídas

```graphql
mutation {
  markAllNotificationsRead {
    success
    message
    count
  }
}
```

**Permisos**: Usuario autenticado (marca sus propias notificaciones)

**Retorna**: Número de notificaciones marcadas

---

### DeleteNotificationMutation
Eliminar notificación

```graphql
mutation {
  deleteNotification(notificationId: "7") {
    success
    message
  }
}
```

**Permisos**: Solo el usuario owner de la notificación

---

### CreateNotificationMutation
Crear notificación manual (Staff only)

```graphql
mutation {
  createNotification(
    userIds: ["1", "2", "3"]
    tipo: "INFO"
    titulo: "Mantenimiento programado"
    mensaje: "El sistema estará en mantenimiento el viernes"
  ) {
    success
    message
    count
  }
}
```

**Permisos**: `@staff_required`

**Tipos válidos**: INFO, ALERTA, EXITO, ERROR

**Retorna**: Número de notificaciones creadas

---

## 8. MÁQUINA DE ESTADOS - PRACTICE

### Estados Disponibles
```python
DRAFT              # Borrador (inicial)
PENDING            # Pendiente de aprobación
APPROVED           # Aprobada
IN_PROGRESS        # En progreso
COMPLETED          # Completada
CANCELLED          # Cancelada
```

### Transiciones Válidas

```
DRAFT ────────────> PENDING          (submit_practice)
  ↑                     │
  │                     │
  │                     ↓
  └──────────────── APPROVED         (approve_practice)
                        │
       (reject)         │
                        ↓
                    IN_PROGRESS       (start_practice)
                        │
                        │
                        ↓
                    COMPLETED         (complete_practice)
```

**Helper Function**:
```python
validate_practice_status_transition(current_status, new_status) -> bool
```

---

## 9. EJEMPLO COMPLETO - FLUJO DE PRÁCTICA

### Paso 1: Crear Empresa
```graphql
mutation {
  createCompany(
    ruc: "20123456789"
    razonSocial: "Tech Corp SAC"
    direccion: "Lima"
    telefono: "014567890"
    email: "info@techcorp.com"
    sectorEconomico: "TI"
    tamañoEmpresa: "MEDIANA"
  ) {
    success
    company { id }
  }
}
```

### Paso 2: Validar Empresa (Coordinador)
```graphql
mutation {
  validateCompany(companyId: "1", status: "ACTIVE") {
    success
  }
}
```

### Paso 3: Crear Supervisor
```graphql
mutation {
  createSupervisor(
    email: "super@techcorp.com"
    firstName: "Carlos"
    lastName: "López"
    password: "Pass123!"
    companyId: "1"
    documentoTipo: "DNI"
    documentoNumero: "12345678"
    cargo: "Jefe TI"
    telefono: "987654321"
  ) {
    success
    supervisor { id }
  }
}
```

### Paso 4: Crear Práctica (Estudiante)
```graphql
mutation {
  createPractice(
    studentId: "1"
    companyId: "1"
    supervisorId: "1"
    tipo: "PREPROFESIONAL"
    area: "Desarrollo"
    fechaInicio: "2024-03-01"
    fechaFin: "2024-08-31"
    horasRequeridas: 640
  ) {
    success
    practice { id status }  # status = DRAFT
  }
}
```

### Paso 5: Enviar a Revisión (Estudiante)
```graphql
mutation {
  submitPractice(practiceId: "1") {
    success
    practice { status }  # status = PENDING
  }
}
```

### Paso 6: Aprobar (Coordinador)
```graphql
mutation {
  approvePractice(practiceId: "1") {
    success
    practice { status }  # status = APPROVED
  }
}
```

### Paso 7: Iniciar (Estudiante/Coordinador)
```graphql
mutation {
  startPractice(practiceId: "1") {
    success
    practice { status }  # status = IN_PROGRESS
  }
}
```

### Paso 8: Subir Documento (Estudiante)
```graphql
mutation {
  createDocument(
    practiceId: "1"
    tipoDocumento: "INFORME_MENSUAL"
    nombre: "Informe Mes 1"
    archivoUrl: "https://..."
  ) {
    success
    document { id status }  # status = PENDING
  }
}
```

### Paso 9: Aprobar Documento (Coordinador)
```graphql
mutation {
  approveDocument(documentId: "1") {
    success
  }
}
```

### Paso 10: Completar (Coordinador)
```graphql
mutation {
  completePractice(practiceId: "1") {
    success
    practice { status }  # status = COMPLETED
  }
}
```

---

## 10. ERRORES COMUNES

### Error: "No tienes permiso"
```json
{
  "success": false,
  "message": "No tienes permiso para crear empresas"
}
```
**Solución**: Verifica que tu usuario tenga el rol adecuado.

### Error: "Email debe ser @upeu.edu.pe"
```json
{
  "success": false,
  "message": "Email debe ser del dominio @upeu.edu.pe"
}
```
**Solución**: Usa email institucional para estudiantes.

### Error: "No se puede aprobar desde estado DRAFT"
```json
{
  "success": false,
  "message": "No se puede aprobar desde estado DRAFT"
}
```
**Solución**: La práctica debe estar en PENDING. Usa `submitPractice` primero.

### Error: "RUC debe tener 11 dígitos"
```json
{
  "success": false,
  "message": "RUC debe tener 11 dígitos numéricos"
}
```
**Solución**: Verifica que el RUC tenga exactamente 11 dígitos.

---

## 11. TESTING

### Ejemplo con curl
```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: JWT your-token-here" \
  -d '{
    "query": "mutation { createStudent(email: \"2024012345@upeu.edu.pe\", firstName: \"Juan\", lastName: \"Pérez\", password: \"Pass123!\", codigo: \"2024012345\", semestre: 6, escuelaProfesional: \"Sistemas\", promedio: 15.0) { success message student { id codigo } } }"
  }'
```

### Ejemplo con GraphQL Client
```javascript
const mutation = gql`
  mutation CreateStudent($input: CreateStudentInput!) {
    createStudent(
      email: $input.email
      firstName: $input.firstName
      lastName: $input.lastName
      password: $input.password
      codigo: $input.codigo
      semestre: $input.semestre
      escuelaProfesional: $input.escuelaProfesional
      promedio: $input.promedio
    ) {
      success
      message
      student {
        id
        codigo
        user {
          fullName
        }
      }
    }
  }
`;

const result = await client.mutate({
  mutation,
  variables: {
    input: {
      email: "2024012345@upeu.edu.pe",
      firstName: "Juan",
      lastName: "Pérez",
      password: "Pass123!",
      codigo: "2024012345",
      semestre: 6,
      escuelaProfesional: "Ingeniería de Sistemas",
      promedio: 15.0
    }
  }
});
```

---

## 12. NOTAS IMPORTANTES

### Autenticación
Todas las mutations requieren autenticación JWT. Incluye el header:
```
Authorization: JWT <tu-token>
```

### Transacciones
Las mutations que crean múltiples objetos (CreateStudentMutation, CreateSupervisorMutation) usan `transaction.atomic()` para garantizar atomicidad.

### Notificaciones
Las notificaciones se generan automáticamente en:
- Cambios de estado de prácticas
- Aprobación/rechazo de documentos
- Creación de empresas
- Asignación de tareas

### Logging
Todos los errores se registran con contexto completo para debugging.

---

## Autor
Sistema de Gestión de Prácticas Profesionales - UPEU  
Fase 4: GraphQL Mutations Completas ✅
