# GraphQL Queries - Sistema de Gestión de Prácticas Profesionales

## Descripción General

Este documento describe todas las queries GraphQL disponibles en el sistema. Las queries están organizadas por entidad e incluyen filtros, búsquedas, paginación y estadísticas.

**Archivo**: `src/adapters/primary/graphql_api/queries_complete.py`

**Total de Queries**: 50+

---

## Características Principales

### 🔒 Control de Permisos
- Validación basada en roles
- Filtrado automático de datos según permisos
- Helpers de permisos reutilizables

### 📄 Paginación
- Información completa de paginación
- Control de tamaño de página
- Navegación entre páginas

### 🔍 Búsquedas Avanzadas
- Búsqueda por múltiples campos
- Filtros combinables
- Ordenamiento personalizado

### 📊 Estadísticas
- Agregaciones en tiempo real
- Métricas por entidad
- Dashboard completo

---

## 1. USER QUERIES

### me
Obtener información del usuario autenticado

```graphql
query {
  me {
    id
    email
    username
    firstName
    lastName
    role
    fullName
    isActive
    photoUrl
    createdAt
  }
}
```

**Permisos**: Usuario autenticado

**Retorna**: Información completa del usuario actual

---

### user
Buscar usuario por ID

```graphql
query {
  user(id: "1") {
    id
    email
    fullName
    role
    isActive
  }
}
```

**Permisos**: Staff (COORDINADOR, SECRETARIA, ADMINISTRADOR)

---

### users (paginado)
Lista paginada de usuarios con filtros

```graphql
query {
  users(
    page: 1
    pageSize: 20
    role: "PRACTICANTE"
    isActive: true
    search: "juan"
  ) {
    items {
      id
      fullName
      email
      role
    }
    pagination {
      page
      pageSize
      totalCount
      totalPages
      hasNext
      hasPrevious
    }
  }
}
```

**Parámetros**:
- `page`: Número de página (default: 1)
- `pageSize`: Elementos por página (default: 20)
- `role`: Filtrar por rol
- `isActive`: Filtrar por estado activo
- `search`: Búsqueda en email, nombre, apellido, username

**Permisos**: ADMINISTRADOR

---

### usersByRole
Usuarios filtrados por rol específico

```graphql
query {
  usersByRole(role: "COORDINADOR") {
    id
    fullName
    email
    isActive
  }
}
```

**Permisos**: Staff

---

### searchUsers
Búsqueda rápida de usuarios (máximo 20 resultados)

```graphql
query {
  searchUsers(query: "perez") {
    id
    fullName
    email
    role
  }
}
```

**Permisos**: Staff

---

## 2. STUDENT QUERIES

### student
Buscar estudiante por ID o código

```graphql
query {
  student(id: "1") {
    id
    codigoEstudiante
    carrera
    semestreActual
    promedioPonderado
    puedeRealizarPractica
    anioIngreso
    user {
      fullName
      email
    }
  }
}

# O por código
query {
  student(codigo: "2024012345") {
    id
    codigoEstudiante
    carrera
  }
}
```

**Permisos**: 
- Staff puede ver cualquier estudiante
- Estudiante puede ver su propio perfil
- Supervisor puede ver estudiantes de sus prácticas

---

### myStudentProfile
Perfil de estudiante del usuario actual

```graphql
query {
  myStudentProfile {
    id
    codigoEstudiante
    carrera
    semestreActual
    promedioPonderado
    puedeRealizarPractica
  }
}
```

**Permisos**: Usuario con rol PRACTICANTE

---

### students (paginado)
Lista paginada de estudiantes

```graphql
query {
  students(
    page: 1
    pageSize: 20
    semestre: 6
    carrera: "Ingeniería de Sistemas"
    search: "garcia"
    orderBy: "-promedio_ponderado"
  ) {
    items {
      id
      codigoEstudiante
      carrera
      semestreActual
      promedioPonderado
      user {
        fullName
      }
    }
    pagination {
      totalCount
      totalPages
      hasNext
    }
  }
}
```

**Parámetros**:
- `page`: Número de página
- `pageSize`: Elementos por página
- `semestre`: Filtrar por semestre
- `carrera`: Filtrar por carrera
- `search`: Búsqueda en código, nombre, carrera
- `orderBy`: Ordenamiento (default: "-created_at")

**Opciones orderBy**:
- `-created_at`: Más recientes primero
- `promedio_ponderado`: Por promedio ascendente
- `-promedio_ponderado`: Por promedio descendente
- `codigo_estudiante`: Por código

**Permisos**: Staff

---

### eligibleStudents
Estudiantes elegibles para prácticas

```graphql
query {
  eligibleStudents {
    id
    codigoEstudiante
    carrera
    semestreActual
    promedioPonderado
    user {
      fullName
      email
    }
  }
}
```

**Criterios de elegibilidad**:
- Semestre >= 6
- Promedio >= 12.0
- Usuario activo

**Ordenamiento**: Por promedio descendente

**Permisos**: Staff

---

### studentsWithoutPractice
Estudiantes sin práctica asignada

```graphql
query {
  studentsWithoutPractice {
    id
    codigoEstudiante
    carrera
    semestreActual
    promedioPonderado
    user {
      fullName
    }
  }
}
```

**Criterios**:
- Elegible para prácticas
- No tiene prácticas en estado APPROVED o IN_PROGRESS

**Permisos**: Staff

---

### searchStudents
Búsqueda rápida de estudiantes

```graphql
query {
  searchStudents(query: "2024") {
    id
    codigoEstudiante
    carrera
    user {
      fullName
    }
  }
}
```

**Busca en**: Código, nombre, apellido, carrera

**Límite**: 20 resultados

**Permisos**: Staff

---

## 3. COMPANY QUERIES

### company
Buscar empresa por ID o RUC

```graphql
query {
  company(id: "1") {
    id
    ruc
    razonSocial
    nombreComercial
    direccion
    telefono
    email
    sectorEconomico
    tamanoEmpresa
    status
    puedeRecibirPracticantes
  }
}

# O por RUC
query {
  company(ruc: "20123456789") {
    id
    razonSocial
    status
  }
}
```

**Permisos**: Cualquier usuario autenticado

---

### companies (paginado)
Lista paginada de empresas

```graphql
query {
  companies(
    page: 1
    pageSize: 20
    status: "ACTIVE"
    sector: "Tecnología"
    search: "tech"
    orderBy: "razon_social"
  ) {
    items {
      id
      razonSocial
      nombreComercial
      sectorEconomico
      status
    }
    pagination {
      totalCount
      totalPages
    }
  }
}
```

**Parámetros**:
- `page`: Número de página
- `pageSize`: Elementos por página
- `status`: ACTIVE, PENDING_VALIDATION, SUSPENDED, BLACKLISTED
- `sector`: Filtrar por sector económico
- `search`: Búsqueda en razón social, nombre comercial, RUC, sector
- `orderBy`: Ordenamiento

**Permisos**: 
- Staff ve todas las empresas
- Otros usuarios solo ven empresas ACTIVE

---

### activeCompanies
Empresas activas que pueden recibir practicantes

```graphql
query {
  activeCompanies {
    id
    razonSocial
    nombreComercial
    sectorEconomico
    direccion
  }
}
```

**Permisos**: Cualquier usuario autenticado

---

### pendingValidationCompanies
Empresas pendientes de validación

```graphql
query {
  pendingValidationCompanies {
    id
    razonSocial
    ruc
    sectorEconomico
    createdAt
  }
}
```

**Permisos**: COORDINADOR, ADMINISTRADOR

---

### companiesBySector
Empresas filtradas por sector económico

```graphql
query {
  companiesBySector(sector: "Tecnología") {
    id
    razonSocial
    nombreComercial
    direccion
  }
}
```

**Permisos**: Cualquier usuario autenticado

---

### searchCompanies
Búsqueda rápida de empresas

```graphql
query {
  searchCompanies(query: "sistemas") {
    id
    razonSocial
    ruc
    sectorEconomico
  }
}
```

**Límite**: 20 resultados

**Permisos**: Cualquier usuario autenticado

---

## 4. SUPERVISOR QUERIES

### supervisor
Buscar supervisor por ID

```graphql
query {
  supervisor(id: "1") {
    id
    cargo
    telefono
    aniosExperiencia
    user {
      fullName
      email
    }
    company {
      razonSocial
    }
  }
}
```

**Permisos**: Staff

---

### mySupervisorProfile
Perfil de supervisor del usuario actual

```graphql
query {
  mySupervisorProfile {
    id
    cargo
    aniosExperiencia
    company {
      razonSocial
      direccion
    }
  }
}
```

**Permisos**: Usuario con rol SUPERVISOR

---

### supervisors
Lista de supervisores (opcionalmente filtrado por empresa)

```graphql
query {
  supervisors(companyId: "1") {
    id
    cargo
    aniosExperiencia
    user {
      fullName
      email
    }
    company {
      razonSocial
    }
  }
}
```

**Permisos**: Staff

---

### companySupervisors
Supervisores de una empresa específica

```graphql
query {
  companySupervisors(companyId: "1") {
    id
    cargo
    user {
      fullName
      email
      isActive
    }
  }
}
```

**Permisos**: Cualquier usuario autenticado

---

### availableSupervisors
Supervisores disponibles (con capacidad)

```graphql
query {
  availableSupervisors(companyId: "1") {
    id
    cargo
    user {
      fullName
    }
  }
}
```

**Criterio de disponibilidad**: Menos de 5 prácticas activas (APPROVED o IN_PROGRESS)

**Ordenamiento**: Por número de prácticas activas (ascendente)

**Permisos**: Cualquier usuario autenticado

---

## 5. PRACTICE QUERIES

### practice
Buscar práctica por ID

```graphql
query {
  practice(id: "1") {
    id
    titulo
    descripcion
    fechaInicio
    fechaFin
    horasTotales
    status
    modalidad
    areaPractica
    duracionDias
    estaActiva
    progresoProcentual
    student {
      codigoEstudiante
      user {
        fullName
      }
    }
    company {
      razonSocial
    }
    supervisor {
      cargo
      user {
        fullName
      }
    }
  }
}
```

**Permisos**: 
- Staff puede ver cualquier práctica
- Estudiante puede ver sus propias prácticas
- Supervisor puede ver prácticas asignadas

---

### practices (paginado)
Lista paginada de prácticas con múltiples filtros

```graphql
query {
  practices(
    page: 1
    pageSize: 20
    status: "IN_PROGRESS"
    studentId: "1"
    companyId: "2"
    supervisorId: "3"
    fechaInicioFrom: "2024-01-01"
    fechaInicioTo: "2024-12-31"
    search: "desarrollo"
    orderBy: "-fecha_inicio"
  ) {
    items {
      id
      titulo
      status
      fechaInicio
      fechaFin
      student {
        user {
          fullName
        }
      }
      company {
        razonSocial
      }
    }
    pagination {
      totalCount
      totalPages
      hasNext
    }
  }
}
```

**Parámetros**:
- `page`: Número de página
- `pageSize`: Elementos por página
- `status`: DRAFT, PENDING, APPROVED, IN_PROGRESS, COMPLETED, CANCELLED
- `studentId`: Filtrar por estudiante
- `companyId`: Filtrar por empresa
- `supervisorId`: Filtrar por supervisor
- `fechaInicioFrom`: Fecha de inicio desde
- `fechaInicioTo`: Fecha de inicio hasta
- `search`: Búsqueda en título, área, empresa, nombre estudiante
- `orderBy`: Ordenamiento

**Permisos**: Según rol del usuario

---

### myPractices
Prácticas del usuario actual

```graphql
query {
  myPractices {
    id
    titulo
    status
    fechaInicio
    fechaFin
    progresoProcentual
    company {
      razonSocial
    }
    supervisor {
      user {
        fullName
      }
    }
  }
}
```

**Permisos**: 
- PRACTICANTE: Sus propias prácticas
- SUPERVISOR: Prácticas asignadas

---

### practicesByStatus
Prácticas filtradas por estado

```graphql
query {
  practicesByStatus(status: "PENDING") {
    id
    titulo
    createdAt
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
```

**Permisos**: Staff o Supervisor (solo sus prácticas)

---

### studentPractices
Prácticas de un estudiante específico

```graphql
query {
  studentPractices(studentId: "1") {
    id
    titulo
    status
    fechaInicio
    fechaFin
    company {
      razonSocial
    }
  }
}
```

**Permisos**: Staff

---

### companyPractices
Prácticas de una empresa específica

```graphql
query {
  companyPractices(companyId: "1") {
    id
    titulo
    status
    student {
      user {
        fullName
      }
    }
    supervisor {
      cargo
    }
  }
}
```

**Permisos**: Staff

---

### supervisorPractices
Prácticas de un supervisor específico

```graphql
query {
  supervisorPractices(supervisorId: "1") {
    id
    titulo
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
```

**Permisos**: Staff

---

### activePractices
Prácticas activas (APPROVED o IN_PROGRESS)

```graphql
query {
  activePractices {
    id
    titulo
    status
    fechaInicio
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
```

**Permisos**: Staff

---

### pendingApprovalPractices
Prácticas pendientes de aprobación

```graphql
query {
  pendingApprovalPractices {
    id
    titulo
    createdAt
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
```

**Permisos**: COORDINADOR, SECRETARIA, ADMINISTRADOR

---

### completedPractices
Prácticas completadas (opcionalmente por año)

```graphql
query {
  completedPractices(year: 2024) {
    id
    titulo
    fechaFin
    calificacionFinal
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
```

**Permisos**: Staff

---

## 6. DOCUMENT QUERIES

### document
Buscar documento por ID

```graphql
query {
  document(id: "1") {
    id
    tipo
    nombreArchivo
    tamanoBytes
    tamanoLegible
    mimeType
    aprobado
    fechaAprobacion
    esImagen
    esPdf
    subidoPor {
      fullName
    }
    practice {
      titulo
    }
  }
}
```

**Permisos**: Staff

---

### documents
Lista de documentos con filtros

```graphql
query {
  documents(
    practiceId: "1"
    tipo: "INFORME_MENSUAL"
    aprobado: false
  ) {
    id
    nombreArchivo
    tipo
    aprobado
    createdAt
  }
}
```

**Permisos**: Staff

---

### practiceDocuments
Documentos de una práctica específica

```graphql
query {
  practiceDocuments(practiceId: "1") {
    id
    tipo
    nombreArchivo
    aprobado
    fechaAprobacion
    subidoPor {
      fullName
    }
  }
}
```

**Permisos**: 
- Staff puede ver cualquier documento
- Estudiante puede ver documentos de sus prácticas
- Supervisor puede ver documentos de sus prácticas

---

### pendingApprovalDocuments
Documentos pendientes de aprobación

```graphql
query {
  pendingApprovalDocuments {
    id
    nombreArchivo
    tipo
    createdAt
    practice {
      titulo
      student {
        user {
          fullName
        }
      }
    }
  }
}
```

**Permisos**: COORDINADOR, SECRETARIA, ADMINISTRADOR

---

### myDocuments
Documentos subidos por el usuario actual

```graphql
query {
  myDocuments {
    id
    nombreArchivo
    tipo
    aprobado
    createdAt
    practice {
      titulo
      company {
        razonSocial
      }
    }
  }
}
```

**Permisos**: Usuario autenticado

---

## 7. NOTIFICATION QUERIES

### myNotifications
Notificaciones del usuario actual

```graphql
query {
  myNotifications(
    leida: false
    tipo: "ALERTA"
    limit: 50
  ) {
    id
    titulo
    mensaje
    tipo
    leida
    fechaLectura
    accionUrl
    esImportante
    createdAt
  }
}
```

**Parámetros**:
- `leida`: Filtrar por leídas/no leídas
- `tipo`: INFO, ALERTA, EXITO, ERROR
- `limit`: Máximo de notificaciones (default: 50)

**Permisos**: Usuario autenticado

---

### unreadNotifications
Notificaciones no leídas

```graphql
query {
  unreadNotifications {
    id
    titulo
    mensaje
    tipo
    createdAt
  }
}
```

**Permisos**: Usuario autenticado

---

### unreadCount
Cantidad de notificaciones no leídas

```graphql
query {
  unreadCount
}
```

**Retorna**: Integer

**Permisos**: Usuario autenticado

---

## 8. STATISTICS QUERIES

### dashboardStatistics
Estadísticas completas del dashboard

```graphql
query {
  dashboardStatistics {
    practices {
      total
      draft
      pending
      approved
      inProgress
      completed
      cancelled
      averageHours
      averageGrade
    }
    students {
      total
      eligible
      withPractice
      withoutPractice
      averageGpa
      bySemester
    }
    companies {
      total
      active
      pending
      suspended
      blacklisted
      bySector
      withPractices
    }
    recentActivities
  }
}
```

**Permisos**: COORDINADOR, SECRETARIA, ADMINISTRADOR

**Incluye**:
- Estadísticas de prácticas por estado
- Promedios de horas y calificaciones
- Estadísticas de estudiantes
- Distribución por semestre
- Estadísticas de empresas
- Distribución por sector
- Últimas 10 actividades del sistema

---

### practiceStatistics
Estadísticas de prácticas (opcionalmente por año)

```graphql
query {
  practiceStatistics(year: 2024) {
    total
    draft
    pending
    approved
    inProgress
    completed
    cancelled
    averageHours
    averageGrade
  }
}
```

**Permisos**: Staff

---

### studentStatistics
Estadísticas de estudiantes

```graphql
query {
  studentStatistics {
    total
    eligible
    withPractice
    withoutPractice
    averageGpa
    bySemester
  }
}
```

**bySemester**: JSON con distribución por semestre (semestre_1 a semestre_12)

**Permisos**: Staff

---

### companyStatistics
Estadísticas de empresas

```graphql
query {
  companyStatistics {
    total
    active
    pending
    suspended
    blacklisted
    bySector
    withPractices
  }
}
```

**bySector**: JSON con distribución por sector económico

**Permisos**: Staff

---

## 9. EJEMPLOS COMPLETOS

### Dashboard Coordinador

```graphql
query CoordinadorDashboard {
  # Usuario actual
  me {
    fullName
    role
  }
  
  # Notificaciones
  unreadCount
  unreadNotifications {
    id
    titulo
    tipo
    createdAt
  }
  
  # Estadísticas
  dashboardStatistics {
    practices {
      total
      pending
      inProgress
      completed
    }
    students {
      total
      eligible
      withoutPractice
    }
    companies {
      active
      pending
    }
    recentActivities
  }
  
  # Prácticas pendientes
  pendingApprovalPractices {
    id
    titulo
    createdAt
    student {
      user {
        fullName
      }
    }
  }
  
  # Documentos pendientes
  pendingApprovalDocuments {
    id
    nombreArchivo
    tipo
    createdAt
  }
}
```

---

### Dashboard Estudiante

```graphql
query EstudianteDashboard {
  # Perfil
  me {
    fullName
    email
  }
  
  myStudentProfile {
    codigoEstudiante
    carrera
    semestreActual
    promedioPonderado
    puedeRealizarPractica
  }
  
  # Notificaciones
  unreadCount
  myNotifications(limit: 10) {
    titulo
    mensaje
    tipo
    createdAt
  }
  
  # Mis prácticas
  myPractices {
    id
    titulo
    status
    fechaInicio
    fechaFin
    progresoProcentual
    company {
      razonSocial
      direccion
    }
    supervisor {
      cargo
      user {
        fullName
        email
      }
    }
  }
  
  # Empresas activas
  activeCompanies {
    id
    razonSocial
    sectorEconomico
  }
}
```

---

### Dashboard Supervisor

```graphql
query SupervisorDashboard {
  # Perfil
  me {
    fullName
  }
  
  mySupervisorProfile {
    cargo
    company {
      razonSocial
      direccion
    }
  }
  
  # Notificaciones
  unreadNotifications {
    titulo
    mensaje
    createdAt
  }
  
  # Mis prácticas supervisadas
  myPractices {
    id
    titulo
    status
    fechaInicio
    fechaFin
    student {
      codigoEstudiante
      user {
        fullName
        email
      }
    }
  }
}
```

---

### Búsqueda Global

```graphql
query GlobalSearch($query: String!) {
  # Buscar estudiantes
  students: searchStudents(query: $query) {
    id
    codigoEstudiante
    carrera
    user {
      fullName
    }
  }
  
  # Buscar empresas
  companies: searchCompanies(query: $query) {
    id
    razonSocial
    ruc
  }
  
  # Buscar usuarios (si es staff)
  users: searchUsers(query: $query) {
    id
    fullName
    email
    role
  }
}
```

**Variables**:
```json
{
  "query": "sistemas"
}
```

---

### Listado con Paginación y Filtros

```graphql
query PracticesList(
  $page: Int!
  $pageSize: Int!
  $status: String
  $search: String
) {
  practices(
    page: $page
    pageSize: $pageSize
    status: $status
    search: $search
    orderBy: "-created_at"
  ) {
    items {
      id
      titulo
      status
      fechaInicio
      fechaFin
      student {
        codigoEstudiante
        user {
          fullName
        }
      }
      company {
        razonSocial
      }
      supervisor {
        user {
          fullName
        }
      }
    }
    pagination {
      page
      pageSize
      totalCount
      totalPages
      hasNext
      hasPrevious
    }
  }
}
```

**Variables**:
```json
{
  "page": 1,
  "pageSize": 20,
  "status": "IN_PROGRESS",
  "search": ""
}
```

---

## 10. OPTIMIZACIÓN Y PERFORMANCE

### Select Related
Todas las queries utilizan `select_related()` para optimizar joins:

```python
# Ejemplo interno
Practice.objects.select_related(
    'student__user',
    'company',
    'supervisor__user'
).all()
```

Esto reduce queries N+1.

---

### Filtros Indexados
Los modelos tienen índices en campos frecuentemente filtrados:
- `codigo_estudiante`
- `ruc`
- `status`
- `created_at`

---

### Límites de Resultados
Queries de búsqueda rápida limitan a 20 resultados automáticamente.

---

## 11. ERRORES COMUNES

### Error: null en campo requerido
```json
{
  "errors": [{
    "message": "Cannot return null for non-nullable field"
  }]
}
```
**Solución**: Verifica que el objeto existe y tienes permisos para verlo.

---

### Error: Sin permisos
La query simplemente retorna lista vacía o `null` según permisos.

---

### Error: Campo no existe
```json
{
  "errors": [{
    "message": "Cannot query field 'campoInvalido' on type 'StudentType'"
  }]
}
```
**Solución**: Verifica el schema de tipos disponibles.

---

## 12. TESTING

### Con curl
```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: JWT your-token-here" \
  -d '{
    "query": "query { me { fullName email role } }"
  }'
```

---

### Con GraphQL Client (JavaScript)
```javascript
const query = gql`
  query GetStudent($id: ID!) {
    student(id: $id) {
      id
      codigoEstudiante
      carrera
      user {
        fullName
      }
    }
  }
`;

const result = await client.query({
  query,
  variables: { id: "1" }
});
```

---

## 13. INTROSPECCIÓN

### Obtener Schema Completo
```graphql
query IntrospectionQuery {
  __schema {
    queryType {
      name
      fields {
        name
        description
        args {
          name
          type {
            name
          }
        }
      }
    }
  }
}
```

---

### Tipos Disponibles
```graphql
query {
  __type(name: "StudentType") {
    name
    fields {
      name
      type {
        name
      }
    }
  }
}
```

---

## Autor
Sistema de Gestión de Prácticas Profesionales - UPEU  
Fase 5: GraphQL Queries Avanzadas ✅
