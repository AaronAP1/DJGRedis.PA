"""
Ejemplo de queries GraphQL para el sistema de gestión de prácticas profesionales.
"""

# =============================================================================
# AUTENTICACIÓN
# =============================================================================

"""
Obtener token JWT (login)
"""
mutation TokenAuth {
  tokenAuth(email: "coordinador@universidad.edu", password: "password123") {
    token
    refreshToken
    user {
      id
      email
      firstName
      lastName
      role
      isActive
    }
  }
}

"""
Verificar token JWT
"""
mutation VerifyToken {
  verifyToken(token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...") {
    payload
  }
}

"""
Refrescar token JWT
"""
mutation RefreshToken {
  refreshToken(refreshToken: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...") {
    token
    refreshToken
  }
}

# =============================================================================
# CONSULTAS (QUERIES)
# =============================================================================

"""
Obtener información del usuario actual
"""
query Me {
  me {
    id
    email
    firstName
    lastName
    role
    isActive
    createdAt
    lastLogin
  }
}

"""
Listar todas las prácticas (con filtros y paginación)
"""
query AllPractices {
  practices(
    first: 20
    after: "cursor_value"
    status: "IN_PROGRESS"
    company_Name_Icontains: "Tech"
  ) {
    edges {
      node {
        id
        titulo
        status
        fechaInicio
        fechaFin
        horasRequeridas
        horasCompletadas
        student {
          id
          codigoEstudiante
          user {
            firstName
            lastName
            email
          }
          carrera
          semestreActual
          promedioPonderado
        }
        company {
          id
          nombre
          ruc
          sector
          email
        }
        supervisor {
          id
          user {
            firstName
            lastName
            email
          }
          cargo
          telefono
        }
        createdAt
        updatedAt
      }
    }
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
  }
}

"""
Obtener mis prácticas (como estudiante o supervisor)
"""
query MyPractices {
  myPractices {
    id
    titulo
    descripcion
    status
    fechaInicio
    fechaFin
    horasRequeridas
    horasCompletadas
    company {
      nombre
      direccion
      telefono
      email
    }
    supervisor {
      user {
        firstName
        lastName
        email
      }
      cargo
      telefono
    }
    documents {
      id
      tipo
      nombre
      descripcion
      archivoUrl
      fechaSubida
      subidoPor {
        firstName
        lastName
      }
    }
  }
}

"""
Listar estudiantes elegibles para prácticas
"""
query EligibleStudents {
  eligibleStudents {
    id
    codigoEstudiante
    user {
      firstName
      lastName
      email
    }
    carrera
    semestreActual
    promedioPonderado
    fechaIngreso
  }
}

"""
Listar empresas activas
"""
query ActiveCompanies {
  activeCompanies {
    id
    nombre
    ruc
    direccion
    telefono
    email
    sector
    descripcion
    status
    fechaRegistro
    supervisors {
      id
      user {
        firstName
        lastName
        email
      }
      cargo
      departamento
    }
  }
}

"""
Obtener estadísticas del sistema
"""
query SystemStatistics {
  statistics
}

"""
Obtener notificaciones no leídas
"""
query UnreadNotifications {
  unreadNotifications {
    id
    tipo
    titulo
    mensaje
    leida
    createdAt
    data
  }
}

"""
Buscar prácticas por múltiples filtros
"""
query SearchPractices($filters: PracticeFilterInput!) {
  practices(
    student_Carrera: $filters.carrera
    status_In: $filters.statusList
    company_Sector: $filters.sector
    fechaInicio_Gte: $filters.fechaDesde
    fechaFin_Lte: $filters.fechaHasta
    first: 50
  ) {
    edges {
      node {
        id
        titulo
        status
        fechaInicio
        fechaFin
        student {
          codigoEstudiante
          user {
            firstName
            lastName
          }
          carrera
        }
        company {
          nombre
          sector
        }
      }
    }
    totalCount
  }
}

# =============================================================================
# MUTACIONES (MUTATIONS)
# =============================================================================

"""
Crear un nuevo usuario
"""
mutation CreateUser($input: UserInput!) {
  createUser(input: $input) {
    success
    message
    user {
      id
      email
      firstName
      lastName
      role
      isActive
      createdAt
    }
  }
}

# Variables:
{
  "input": {
    "email": "nuevo.estudiante@universidad.edu",
    "password": "password123",
    "firstName": "Juan",
    "lastName": "Pérez",
    "role": "PRACTICANTE"
  }
}

"""
Crear un nuevo estudiante
"""
mutation CreateStudent($input: StudentInput!) {
  createStudent(input: $input) {
    success
    message
    student {
      id
      codigoEstudiante
      dni
      user {
        firstName
        lastName
        email
      }
      carrera
      semestreActual
      promedioPonderado
    }
  }
}

# Variables:
{
  "input": {
    "userId": "user-uuid-here",
    "codigoEstudiante": "2024123456",
    "dni": "12345678",
    "fechaNacimiento": "2000-05-15",
    "telefono": "+51987654321",
    "direccion": "Av. Universitaria 123, Lima",
    "carrera": "Ingeniería de Sistemas",
    "semestreActual": 8,
    "promedioPonderado": 15.5,
    "fechaIngreso": "2020-03-01"
  }
}

"""
Crear una nueva empresa
"""
mutation CreateCompany($input: CompanyInput!) {
  createCompany(input: $input) {
    success
    message
    company {
      id
      nombre
      ruc
      direccion
      telefono
      email
      sector
      status
      fechaRegistro
    }
  }
}

# Variables:
{
  "input": {
    "nombre": "TechCorp SAC",
    "ruc": "20123456789",
    "direccion": "Av. Tecnología 456, San Isidro",
    "telefono": "+5114567890",
    "email": "contacto@techcorp.com",
    "sector": "Tecnología",
    "descripcion": "Empresa de desarrollo de software"
  }
}

"""
Crear una nueva práctica
"""
mutation CreatePractice($input: PracticeInput!) {
  createPractice(input: $input) {
    success
    message
    practice {
      id
      titulo
      descripcion
      status
      fechaInicio
      fechaFin
      horasRequeridas
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
}

# Variables:
{
  "input": {
    "studentId": "student-uuid-here",
    "companyId": "company-uuid-here",
    "supervisorId": "supervisor-uuid-here",
    "titulo": "Desarrollo de Sistema Web",
    "descripcion": "Desarrollo de aplicación web para gestión de inventarios",
    "fechaInicio": "2024-03-01",
    "fechaFin": "2024-08-31",
    "horasRequeridas": 480
  }
}

"""
Actualizar estado de una práctica
"""
mutation UpdatePracticeStatus($practiceId: ID!, $status: String!, $observations: String) {
  updatePracticeStatus(
    practiceId: $practiceId
    status: $status
    observations: $observations
  ) {
    success
    message
    practice {
      id
      titulo
      status
      observaciones
      fechaAprobacion
      aprobadoPor {
        firstName
        lastName
      }
    }
  }
}

# Variables:
{
  "practiceId": "practice-uuid-here",
  "status": "APPROVED",
  "observations": "Práctica aprobada, cumple con todos los requisitos"
}

"""
Validar una empresa
"""
mutation ValidateCompany($companyId: ID!, $approve: Boolean!, $observations: String) {
  validateCompany(
    companyId: $companyId
    approve: $approve
    observations: $observations
  ) {
    success
    message
    company {
      id
      nombre
      status
      fechaAprobacion
      observaciones
      aprobadoPor {
        firstName
        lastName
      }
    }
  }
}

# Variables:
{
  "companyId": "company-uuid-here",
  "approve": true,
  "observations": "Empresa validada exitosamente"
}

"""
Subir un documento
"""
mutation UploadDocument($input: DocumentInput!) {
  uploadDocument(input: $input) {
    success
    message
    document {
      id
      tipo
      nombre
      descripcion
      archivoUrl
      fechaSubida
      subidoPor {
        firstName
        lastName
      }
    }
  }
}

# Variables:
{
  "input": {
    "practiceId": "practice-uuid-here",
    "tipo": "INFORME_FINAL",
    "nombre": "Informe Final de Prácticas",
    "descripcion": "Documento que describe las actividades realizadas",
    "archivoUrl": "https://storage.example.com/documents/informe_final.pdf"
  }
}

"""
Marcar notificación como leída
"""
mutation MarkNotificationAsRead($notificationId: ID!) {
  markNotificationAsRead(notificationId: $notificationId) {
    success
    message
    notification {
      id
      leida
      fechaLectura
    }
  }
}

# =============================================================================
# QUERIES COMPLEJAS CON MÚLTIPLES RELACIONES
# =============================================================================

"""
Dashboard completo para coordinador
"""
query CoordinatorDashboard {
  # Estadísticas generales
  statistics
  
  # Prácticas pendientes de aprobación
  practices(status: "PENDING", first: 10) {
    edges {
      node {
        id
        titulo
        student {
          codigoEstudiante
          user {
            firstName
            lastName
          }
        }
        company {
          nombre
        }
        fechaInicio
        createdAt
      }
    }
  }
  
  # Empresas pendientes de validación
  companies(status: "PENDING_VALIDATION", first: 5) {
    edges {
      node {
        id
        nombre
        ruc
        sector
        fechaRegistro
      }
    }
  }
  
  # Notificaciones no leídas
  unreadNotifications {
    id
    tipo
    titulo
    mensaje
    createdAt
  }
}

"""
Perfil completo de estudiante con historial
"""
query StudentProfile($studentId: ID!) {
  student(id: $studentId) {
    id
    codigoEstudiante
    dni
    fechaNacimiento
    telefono
    direccion
    carrera
    semestreActual
    promedioPonderado
    fechaIngreso
    user {
      id
      email
      firstName
      lastName
      isActive
      lastLogin
    }
    practices {
      id
      titulo
      status
      fechaInicio
      fechaFin
      horasRequeridas
      horasCompletadas
      company {
        nombre
        sector
      }
      supervisor {
        user {
          firstName
          lastName
        }
        cargo
      }
      documents {
        id
        tipo
        nombre
        fechaSubida
      }
    }
  }
}

# =============================================================================
# SUBSCRIPTIONS (TIEMPO REAL) - OPCIONAL
# =============================================================================

"""
Suscribirse a cambios en prácticas
"""
subscription PracticeUpdates($userId: ID!) {
  practiceUpdates(userId: $userId) {
    id
    titulo
    status
    updatedAt
    message
  }
}

"""
Suscribirse a nuevas notificaciones
"""
subscription NewNotifications($userId: ID!) {
  newNotifications(userId: $userId) {
    id
    tipo
    titulo
    mensaje
    createdAt
  }
}
