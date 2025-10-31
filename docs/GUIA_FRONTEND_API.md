# 🎨 Guía de API para Frontend - Sistema de Prácticas Profesionales

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Autenticación](#autenticación)
3. [Estructura de Respuestas](#estructura-de-respuestas)
4. [Endpoints por Módulo](#endpoints-por-módulo)
5. [Flujos Completos](#flujos-completos)
6. [Manejo de Errores](#manejo-de-errores)
7. [Ejemplos de Código](#ejemplos-de-código)
8. [Testing con Swagger](#testing-con-swagger)

---

## 🎯 Introducción

Esta guía te ayudará a integrar el frontend con la API del sistema de prácticas profesionales.

### URLs Base

| Ambiente | URL | Descripción |
|----------|-----|-------------|
| **Desarrollo** | `http://localhost:8000` | Local |
| **Azure** | `https://upeu-ppp-api-5983.azurewebsites.net` | Producción |
| **Documentación** | `/api/docs/` | Scalar UI interactivo |
| **Testing** | `/api/swagger/` | Swagger UI |

### Tecnologías de API

- **REST API**: Endpoints estándar con JSON
- **GraphQL**: Queries y mutations flexibles
- **Autenticación**: JWT (JSON Web Tokens)
- **Formato**: JSON exclusivamente

---

## 🔐 Autenticación

### 1. Login (Obtener Token)

**Endpoint**: `POST /api/v2/auth/login/`

**Request Body**:
```json
{
  "email": "estudiante@upeu.edu.pe",
  "password": "tu_password"
}
```

**Response Success (200)**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",  // Token de acceso (1 hora)
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbG...", // Token refresh (7 días)
  "user": {
    "id": 1,
    "email": "estudiante@upeu.edu.pe",
    "nombre": "Juan Pérez",
    "role": "PRACTICANTE"
  }
}
```

**Ejemplo JavaScript**:
```javascript
const login = async (email, password) => {
  const response = await fetch('https://upeu-ppp-api-5983.azurewebsites.net/api/v2/auth/login/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Guardar tokens en localStorage
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data;
  } else {
    throw new Error(data.detail || 'Error al iniciar sesión');
  }
};
```

### 2. Usar el Token en Requests

**Todas las peticiones autenticadas deben incluir el header**:

```javascript
headers: {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${localStorage.getItem('access_token')}`
}
```

### 3. Refresh Token

**Endpoint**: `POST /api/v2/auth/refresh/`

Cuando el access token expire (1 hora), usa el refresh token:

```javascript
const refreshToken = async () => {
  const response = await fetch('https://upeu-ppp-api-5983.azurewebsites.net/api/v2/auth/refresh/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      refresh: localStorage.getItem('refresh_token')
    })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    localStorage.setItem('access_token', data.access);
    return data.access;
  } else {
    // Token refresh expirado, re-login requerido
    window.location.href = '/login';
  }
};
```

### 4. Logout

**Endpoint**: `POST /api/v2/auth/logout/`

```javascript
const logout = async () => {
  await fetch('https://upeu-ppp-api-5983.azurewebsites.net/api/v2/auth/logout/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  
  // Limpiar localStorage
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  
  window.location.href = '/login';
};
```

---

## 📦 Estructura de Respuestas

### Respuesta Exitosa (200-201)

```json
{
  "id": 1,
  "titulo": "Práctica en Desarrollo Web",
  "status": "PENDING",
  "created_at": "2024-10-30T10:00:00Z",
  // ... más campos
}
```

### Respuesta con Lista Paginada

```json
{
  "count": 25,           // Total de elementos
  "next": "http://api.../practices/?page=2",
  "previous": null,
  "results": [           // Array de objetos
    {
      "id": 1,
      "titulo": "Práctica 1",
      // ...
    },
    // ...
  ]
}
```

### Respuesta de Error (400, 401, 403, 404, 500)

```json
{
  "detail": "No tiene permisos para realizar esta acción",
  "code": "permission_denied"
}
```

O con validaciones:

```json
{
  "horas_totales": ["Este campo debe ser al menos 480"],
  "fecha_fin": ["La fecha fin debe ser posterior a la fecha inicio"]
}
```

---

## 🚀 Endpoints por Módulo

### 📝 PRÁCTICAS

#### 1. Listar Prácticas

**GET** `/api/v2/practices/`

**Query Params**:
- `status`: Filtrar por estado (`DRAFT`, `PENDING`, `APPROVED`, etc.)
- `search`: Búsqueda por título, empresa, estudiante
- `page`: Número de página (default: 1)
- `page_size`: Resultados por página (default: 10)

**Ejemplo**:
```javascript
const getPractices = async (filters = {}) => {
  const params = new URLSearchParams(filters);
  
  const response = await fetch(
    `https://upeu-ppp-api-5983.azurewebsites.net/api/v2/practices/?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  
  return response.json();
};

// Uso:
const practices = await getPractices({ status: 'PENDING', page: 1 });
```

**Response**:
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "titulo": "Práctica en Desarrollo Web",
      "status": "PENDING",
      "student": {
        "id": 10,
        "user": {
          "nombre": "Juan Pérez",
          "email": "juan@upeu.edu.pe"
        },
        "codigo_estudiante": "2020123456"
      },
      "company": {
        "id": 5,
        "razon_social": "Tech Solutions SAC",
        "ruc": "20123456789"
      },
      "supervisor": {
        "id": 3,
        "user": {
          "nombre": "Carlos Supervisor"
        }
      },
      "fecha_inicio": "2024-11-01",
      "fecha_fin": "2025-02-28",
      "horas_totales": 480,
      "horas_completadas": 120,
      "progreso_porcentual": 25.0,
      "area_practica": "Desarrollo Backend",
      "modalidad": "PRESENCIAL",
      "created_at": "2024-10-15T10:00:00Z"
    }
  ]
}
```

#### 2. Ver Detalle de Práctica

**GET** `/api/v2/practices/{id}/`

```javascript
const getPracticeDetail = async (practiceId) => {
  const response = await fetch(
    `https://upeu-ppp-api-5983.azurewebsites.net/api/v2/practices/${practiceId}/`,
    {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  
  return response.json();
};
```

**Response**:
```json
{
  "id": 1,
  "titulo": "Práctica en Desarrollo Web",
  "descripcion": "Desarrollo de aplicaciones web con Django",
  "objetivos": [
    "Aprender Django REST Framework",
    "Implementar autenticación JWT",
    "Desarrollar APIs RESTful"
  ],
  "status": "IN_PROGRESS",
  "student": {
    "id": 10,
    "user": {
      "id": 15,
      "email": "juan@upeu.edu.pe",
      "nombre": "Juan",
      "apellido": "Pérez",
      "telefono": "987654321"
    },
    "codigo_estudiante": "2020123456",
    "carrera_profesional": "Ingeniería de Sistemas",
    "semestre_actual": 8,
    "promedio_ponderado": 15.5
  },
  "company": {
    "id": 5,
    "razon_social": "Tech Solutions SAC",
    "ruc": "20123456789",
    "sector": "Tecnología",
    "direccion": "Av. Arequipa 123, Lima",
    "telefono": "014567890",
    "email": "info@techsolutions.com"
  },
  "supervisor": {
    "id": 3,
    "user": {
      "nombre": "Carlos",
      "apellido": "Supervisor",
      "email": "carlos@techsolutions.com"
    },
    "cargo": "Jefe de Desarrollo",
    "telefono": "987123456"
  },
  "fecha_inicio": "2024-11-01",
  "fecha_fin": "2025-02-28",
  "horas_totales": 480,
  "horas_completadas": 120,
  "progreso_porcentual": 25.0,
  "area_practica": "Desarrollo Backend",
  "modalidad": "PRESENCIAL",
  "calificacion_final": null,
  "observaciones": "",
  "created_at": "2024-10-15T10:00:00Z",
  "updated_at": "2024-10-30T08:30:00Z"
}
```

#### 3. Crear Nueva Práctica

**POST** `/api/v2/practices/`

```javascript
const createPractice = async (practiceData) => {
  const response = await fetch(
    'https://upeu-ppp-api-5983.azurewebsites.net/api/v2/practices/',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify(practiceData)
    }
  );
  
  return response.json();
};

// Uso:
const newPractice = await createPractice({
  titulo: "Práctica en Desarrollo Web",
  descripcion: "Desarrollo de aplicaciones web modernas",
  company: 5,              // ID de la empresa
  supervisor: 3,           // ID del supervisor
  fecha_inicio: "2024-11-01",
  fecha_fin: "2025-02-28",
  horas_totales: 480,
  area_practica: "Desarrollo Backend",
  modalidad: "PRESENCIAL",
  objetivos: [
    "Aprender Django",
    "Implementar APIs REST"
  ]
});
```

**Response (201)**:
```json
{
  "id": 25,
  "titulo": "Práctica en Desarrollo Web",
  "status": "DRAFT",  // Estado inicial
  "message": "Práctica creada exitosamente"
}
```

#### 4. Actualizar Práctica

**PUT/PATCH** `/api/v2/practices/{id}/`

```javascript
const updatePractice = async (practiceId, updates) => {
  const response = await fetch(
    `https://upeu-ppp-api-5983.azurewebsites.net/api/v2/practices/${practiceId}/`,
    {
      method: 'PATCH',  // PATCH para actualización parcial
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify(updates)
    }
  );
  
  return response.json();
};

// Uso - Solo actualizar título y descripción:
await updatePractice(25, {
  titulo: "Práctica Actualizada",
  descripcion: "Nueva descripción"
});
```

#### 5. Enviar Práctica a Revisión

**POST** `/api/v2/practices/{id}/submit/`

```javascript
const submitPractice = async (practiceId) => {
  const response = await fetch(
    `https://upeu-ppp-api-5983.azurewebsites.net/api/v2/practices/${practiceId}/submit/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  
  return response.json();
};
```

**Response**:
```json
{
  "message": "Práctica enviada a revisión",
  "practice": {
    "id": 25,
    "status": "PENDING"  // Estado cambió de DRAFT a PENDING
  }
}
```

#### 6. Aprobar Práctica (Solo COORDINADOR)

**POST** `/api/v2/practices/{id}/approve/`

```javascript
const approvePractice = async (practiceId, supervisorId) => {
  const response = await fetch(
    `https://upeu-ppp-api-5983.azurewebsites.net/api/v2/practices/${practiceId}/approve/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({
        supervisor_id: supervisorId  // Opcional, asignar supervisor
      })
    }
  );
  
  return response.json();
};
```

#### 7. Iniciar Práctica

**POST** `/api/v2/practices/{id}/start/`

```javascript
const startPractice = async (practiceId) => {
  const response = await fetch(
    `https://upeu-ppp-api-5983.azurewebsites.net/api/v2/practices/${practiceId}/start/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  
  return response.json();
};
```

#### 8. Completar Práctica (Solo COORDINADOR)

**POST** `/api/v2/practices/{id}/complete/`

```javascript
const completePractice = async (practiceId, calificacion, observaciones) => {
  const response = await fetch(
    `https://upeu-ppp-api-5983.azurewebsites.net/api/v2/practices/${practiceId}/complete/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({
        calificacion_final: calificacion,  // 0-20
        observaciones: observaciones
      })
    }
  );
  
  return response.json();
};
```

### 👤 ESTUDIANTES

#### Listar Estudiantes

**GET** `/api/v2/students/`

```javascript
const getStudents = async () => {
  const response = await fetch(
    'https://upeu-ppp-api-5983.azurewebsites.net/api/v2/students/',
    {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  
  return response.json();
};
```

### 🏢 EMPRESAS

#### Listar Empresas

**GET** `/api/v2/companies/`

```javascript
const getCompanies = async (filters = {}) => {
  const params = new URLSearchParams(filters);
  
  const response = await fetch(
    `https://upeu-ppp-api-5983.azurewebsites.net/api/v2/companies/?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  
  return response.json();
};

// Filtros disponibles:
// - status: ACTIVE, INACTIVE
// - sector: Tecnología, Educación, etc.
// - search: Buscar por nombre o RUC
```

#### Crear Empresa

**POST** `/api/v2/companies/`

```javascript
const createCompany = async (companyData) => {
  const response = await fetch(
    'https://upeu-ppp-api-5983.azurewebsites.net/api/v2/companies/',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify(companyData)
    }
  );
  
  return response.json();
};

// Uso:
await createCompany({
  razon_social: "Tech Solutions SAC",
  ruc: "20123456789",
  sector: "Tecnología",
  direccion: "Av. Arequipa 123",
  telefono: "014567890",
  email: "info@techsolutions.com"
});
```

### 📄 DOCUMENTOS

#### Subir Documento

**POST** `/api/v2/documents/`

```javascript
const uploadDocument = async (practiceId, file, tipo) => {
  const formData = new FormData();
  formData.append('practice', practiceId);
  formData.append('archivo', file);  // File object del input
  formData.append('tipo_documento', tipo);  // CARTA_PRESENTACION, INFORME, etc.
  formData.append('descripcion', 'Descripción del documento');
  
  const response = await fetch(
    'https://upeu-ppp-api-5983.azurewebsites.net/api/v2/documents/',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        // NO incluir Content-Type, el navegador lo configura automáticamente
      },
      body: formData
    }
  );
  
  return response.json();
};

// Uso en React:
const handleFileUpload = async (e) => {
  const file = e.target.files[0];
  const result = await uploadDocument(practiceId, file, 'INFORME');
  console.log('Documento subido:', result);
};
```

#### Listar Documentos de una Práctica

**GET** `/api/v2/practices/{id}/documents/`

```javascript
const getPracticeDocuments = async (practiceId) => {
  const response = await fetch(
    `https://upeu-ppp-api-5983.azurewebsites.net/api/v2/practices/${practiceId}/documents/`,
    {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  
  return response.json();
};
```

### 📊 DASHBOARDS

#### Dashboard del Coordinador

**GET** `/api/v2/dashboards/coordinator/`

```javascript
const getCoordinatorDashboard = async () => {
  const response = await fetch(
    'https://upeu-ppp-api-5983.azurewebsites.net/api/v2/dashboards/coordinator/',
    {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  
  return response.json();
};
```

**Response**:
```json
{
  "total_practices": 45,
  "practices_by_status": {
    "DRAFT": 5,
    "PENDING": 8,
    "APPROVED": 10,
    "IN_PROGRESS": 15,
    "COMPLETED": 7
  },
  "total_students": 120,
  "total_companies": 30,
  "active_practices": 15,
  "recent_practices": [
    {
      "id": 1,
      "titulo": "...",
      "student": {...},
      "status": "PENDING"
    }
  ],
  "pending_approvals": [...]
}
```

#### Dashboard del Estudiante

**GET** `/api/v2/dashboards/student/`

```javascript
const getStudentDashboard = async () => {
  const response = await fetch(
    'https://upeu-ppp-api-5983.azurewebsites.net/api/v2/dashboards/student/',
    {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  
  return response.json();
};
```

**Response**:
```json
{
  "my_practice": {
    "id": 25,
    "titulo": "Práctica en Desarrollo Web",
    "status": "IN_PROGRESS",
    "progreso_porcentual": 35.5,
    "horas_completadas": 170,
    "horas_totales": 480
  },
  "notifications": [...],
  "pending_documents": [...]
}
```

### 📈 REPORTES

#### Descargar Certificado

**GET** `/api/v2/reports/{practice_id}/certificate/`

```javascript
const downloadCertificate = async (practiceId) => {
  const response = await fetch(
    `https://upeu-ppp-api-5983.azurewebsites.net/api/v2/reports/${practiceId}/certificate/`,
    {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  
  // Convertir a blob para descarga
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `certificado-practica-${practiceId}.pdf`;
  a.click();
};
```

---

## 🔄 Flujos Completos

### Flujo 1: Crear y Enviar Práctica (Estudiante)

```javascript
// Paso 1: Crear práctica
const practice = await createPractice({
  titulo: "Práctica en Desarrollo Web",
  company: 5,
  supervisor: 3,
  fecha_inicio: "2024-11-01",
  fecha_fin: "2025-02-28",
  horas_totales: 480,
  area_practica: "Backend",
  modalidad: "PRESENCIAL"
});
// Estado: DRAFT

// Paso 2: Subir documentos requeridos
await uploadDocument(practice.id, cartaPresentacion, 'CARTA_PRESENTACION');
await uploadDocument(practice.id, cartaAceptacion, 'CARTA_ACEPTACION');
await uploadDocument(practice.id, planTrabajo, 'PLAN_TRABAJO');

// Paso 3: Enviar a revisión
await submitPractice(practice.id);
// Estado: PENDING

// Paso 4: Esperar aprobación del coordinador
```

### Flujo 2: Aprobar Práctica (Coordinador)

```javascript
// Paso 1: Obtener prácticas pendientes
const practices = await getPractices({ status: 'PENDING' });

// Paso 2: Ver detalle
const detail = await getPracticeDetail(practices.results[0].id);

// Paso 3: Aprobar
await approvePractice(detail.id, supervisorId);
// Estado: APPROVED

// El estudiante recibe notificación
```

### Flujo 3: Ejecutar Práctica (Estudiante + Supervisor)

```javascript
// Estudiante inicia práctica
await startPractice(practiceId);
// Estado: IN_PROGRESS

// Durante la práctica:
// - Estudiante sube informes mensuales
await uploadDocument(practiceId, informeMes1, 'INFORME');

// - Supervisor revisa y aprueba documentos
// - Se registran horas trabajadas
```

### Flujo 4: Completar Práctica (Coordinador)

```javascript
// Coordinador completa y califica
await completePractice(practiceId, 18.5, "Excelente desempeño");
// Estado: COMPLETED

// Estudiante puede descargar certificado
await downloadCertificate(practiceId);
```

---

## ⚠️ Manejo de Errores

### Errores Comunes

```javascript
const handleApiCall = async (apiFunction) => {
  try {
    const result = await apiFunction();
    return result;
  } catch (error) {
    // Error de red
    if (!error.response) {
      console.error('Error de conexión:', error);
      alert('Error de conexión. Verifica tu internet.');
      return;
    }
    
    // Errores HTTP
    switch (error.response.status) {
      case 400:
        // Validación fallida
        console.error('Datos inválidos:', error.response.data);
        alert('Por favor revisa los datos ingresados');
        break;
        
      case 401:
        // Token expirado o inválido
        console.error('No autenticado');
        await refreshToken();  // Intentar refresh
        break;
        
      case 403:
        // Sin permisos
        console.error('Sin permisos:', error.response.data);
        alert('No tienes permisos para esta acción');
        break;
        
      case 404:
        // Recurso no encontrado
        console.error('No encontrado:', error.response.data);
        alert('El recurso solicitado no existe');
        break;
        
      case 500:
        // Error del servidor
        console.error('Error del servidor:', error.response.data);
        alert('Error del servidor. Contacta al administrador');
        break;
        
      default:
        console.error('Error:', error.response.data);
    }
  }
};
```

### Validación de Campos

```javascript
// Ejemplo de manejo de errores de validación
const createPractice = async (data) => {
  try {
    const response = await fetch('/api/v2/practices/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    });
    
    const result = await response.json();
    
    if (!response.ok) {
      // result contiene los errores de validación
      // Formato: { "campo": ["mensaje de error"] }
      Object.keys(result).forEach(field => {
        console.error(`Error en ${field}:`, result[field]);
      });
      return { success: false, errors: result };
    }
    
    return { success: true, data: result };
    
  } catch (error) {
    console.error('Error:', error);
    return { success: false, errors: { general: ['Error de conexión'] } };
  }
};
```

---

## 💻 Ejemplos de Código Completo

### React Hook Personalizado

```javascript
// hooks/useApi.js
import { useState, useEffect } from 'react';

const API_BASE_URL = 'https://upeu-ppp-api-5983.azurewebsites.net/api/v2';

export const useApi = (endpoint, options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
          ...options
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        setData(result);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [endpoint]);
  
  return { data, loading, error };
};

// Uso:
function PracticesList() {
  const { data, loading, error } = useApi('/practices/');
  
  if (loading) return <div>Cargando...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div>
      {data.results.map(practice => (
        <div key={practice.id}>{practice.titulo}</div>
      ))}
    </div>
  );
}
```

### Servicio de API Completo (Vanilla JS)

```javascript
// services/api.js
class ApiService {
  constructor() {
    this.baseURL = 'https://upeu-ppp-api-5983.azurewebsites.net/api/v2';
  }
  
  getToken() {
    return localStorage.getItem('access_token');
  }
  
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    
    if (this.getToken()) {
      headers['Authorization'] = `Bearer ${this.getToken()}`;
    }
    
    const config = {
      ...options,
      headers,
    };
    
    try {
      const response = await fetch(url, config);
      const data = await response.json();
      
      if (!response.ok) {
        throw { status: response.status, data };
      }
      
      return data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }
  
  // Métodos de autenticación
  async login(email, password) {
    const data = await this.request('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    localStorage.setItem('user', JSON.stringify(data.user));
    
    return data;
  }
  
  async logout() {
    await this.request('/auth/logout/', { method: 'POST' });
    localStorage.clear();
  }
  
  // Métodos de prácticas
  async getPractices(filters = {}) {
    const params = new URLSearchParams(filters);
    return this.request(`/practices/?${params}`);
  }
  
  async getPractice(id) {
    return this.request(`/practices/${id}/`);
  }
  
  async createPractice(data) {
    return this.request('/practices/', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
  
  async updatePractice(id, data) {
    return this.request(`/practices/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  }
  
  async submitPractice(id) {
    return this.request(`/practices/${id}/submit/`, {
      method: 'POST'
    });
  }
  
  async approvePractice(id, supervisorId) {
    return this.request(`/practices/${id}/approve/`, {
      method: 'POST',
      body: JSON.stringify({ supervisor_id: supervisorId })
    });
  }
  
  async startPractice(id) {
    return this.request(`/practices/${id}/start/`, {
      method: 'POST'
    });
  }
  
  async completePractice(id, calificacion, observaciones) {
    return this.request(`/practices/${id}/complete/`, {
      method: 'POST',
      body: JSON.stringify({ calificacion_final: calificacion, observaciones })
    });
  }
  
  // Métodos de documentos
  async uploadDocument(practiceId, file, tipo, descripcion) {
    const formData = new FormData();
    formData.append('practice', practiceId);
    formData.append('archivo', file);
    formData.append('tipo_documento', tipo);
    formData.append('descripcion', descripcion);
    
    return this.request('/documents/', {
      method: 'POST',
      headers: {}, // No Content-Type para FormData
      body: formData
    });
  }
  
  async getPracticeDocuments(practiceId) {
    return this.request(`/practices/${practiceId}/documents/`);
  }
  
  // Dashboards
  async getCoordinatorDashboard() {
    return this.request('/dashboards/coordinator/');
  }
  
  async getStudentDashboard() {
    return this.request('/dashboards/student/');
  }
  
  async getSupervisorDashboard() {
    return this.request('/dashboards/supervisor/');
  }
}

// Exportar instancia única
export const api = new ApiService();

// Uso:
import { api } from './services/api';

const practices = await api.getPractices({ status: 'PENDING' });
```

---

## 🧪 Testing con Swagger

### Acceder a Swagger UI

1. Abre tu navegador en: `https://upeu-ppp-api-5983.azurewebsites.net/api/swagger/`

### Autenticarse en Swagger

1. Haz login primero usando el endpoint `/api/v2/auth/login/`
2. Copia el token `access` de la respuesta
3. Haz clic en el botón **"Authorize"** (candado verde arriba a la derecha)
4. Ingresa: `Bearer TU_ACCESS_TOKEN`
5. Clic en **"Authorize"**
6. Ahora puedes probar todos los endpoints

### Probar un Endpoint

1. Selecciona el endpoint (ej: `GET /api/v2/practices/`)
2. Clic en **"Try it out"**
3. Modifica parámetros si es necesario
4. Clic en **"Execute"**
5. Ver la respuesta abajo

---

## 📚 Recursos Adicionales

### Documentación Interactiva

- **Scalar UI**: `https://upeu-ppp-api-5983.azurewebsites.net/api/docs/`
  - Más moderna y fácil de usar
  - Ejemplos de código automáticos
  - Testing integrado

- **Swagger UI**: `https://upeu-ppp-api-5983.azurewebsites.net/api/swagger/`
  - Documentación OpenAPI estándar
  - Testing de endpoints
  - Esquemas de datos

### Tipos de Documentos

```javascript
const TIPOS_DOCUMENTO = {
  CARTA_PRESENTACION: 'CARTA_PRESENTACION',
  CARTA_ACEPTACION: 'CARTA_ACEPTACION',
  PLAN_TRABAJO: 'PLAN_TRABAJO',
  CONVENIO: 'CONVENIO',
  INFORME: 'INFORME',
  CERTIFICADO: 'CERTIFICADO',
  EVALUACION: 'EVALUACION',
  OTRO: 'OTRO'
};
```

### Estados de Práctica

```javascript
const PRACTICE_STATUS = {
  DRAFT: 'DRAFT',           // Borrador
  PENDING: 'PENDING',       // Pendiente aprobación
  APPROVED: 'APPROVED',     // Aprobada
  IN_PROGRESS: 'IN_PROGRESS', // En progreso
  COMPLETED: 'COMPLETED',   // Completada
  CANCELLED: 'CANCELLED',   // Cancelada
  SUSPENDED: 'SUSPENDED'    // Suspendida
};
```

### Roles de Usuario

```javascript
const USER_ROLES = {
  PRACTICANTE: 'PRACTICANTE',     // Estudiante
  SUPERVISOR: 'SUPERVISOR',       // Supervisor empresa
  COORDINADOR: 'COORDINADOR',     // Coordinador académico
  SECRETARIA: 'SECRETARIA',       // Personal administrativo
  ADMINISTRADOR: 'ADMINISTRADOR'  // Admin sistema
};
```

---

## 🎯 Checklist de Integración

### Frontend debe implementar:

- [ ] Sistema de autenticación con JWT
- [ ] Refresh automático de tokens
- [ ] Manejo de errores por código HTTP
- [ ] Loading states durante requests
- [ ] Validación de formularios
- [ ] Subida de archivos con FormData
- [ ] Paginación de listas
- [ ] Filtros y búsqueda
- [ ] Notificaciones de usuario
- [ ] Redirección según rol de usuario

### Componentes sugeridos:

- [ ] Login/Register forms
- [ ] Dashboard por rol (Estudiante, Supervisor, Coordinador)
- [ ] Lista de prácticas con filtros
- [ ] Formulario crear/editar práctica
- [ ] Visualización de detalle de práctica
- [ ] Subida de documentos
- [ ] Lista de documentos
- [ ] Barra de progreso de horas
- [ ] Sistema de notificaciones
- [ ] Descarga de certificados

---

## 🚨 Notas Importantes

1. **CORS**: Ya está configurado en el backend para aceptar requests del frontend

2. **Rate Limiting**: Máximo 100 requests por minuto por IP

3. **Tamaño de archivos**: Máximo 5MB por documento

4. **Formatos aceptados**: PDF, DOC, DOCX, JPG, PNG

5. **Tokens**:
   - Access token expira en 1 hora
   - Refresh token expira en 7 días
   - Implementar refresh automático

6. **Paginación**: Default 10 items por página, máximo 100

7. **Fechas**: Formato ISO 8601 (`YYYY-MM-DD`)

8. **Códigos de estudiante**: Formato `YYYY######` (año + 6 dígitos)

9. **RUC**: Exactamente 11 dígitos numéricos

10. **Calificaciones**: Rango 0-20 (sistema vigesimal peruano)

---

**¿Necesitas ayuda?**

- Revisa la documentación interactiva: `/api/docs/`
- Prueba endpoints en Swagger: `/api/swagger/`
- Contacta al equipo de backend para dudas específicas

---

**Sistema de Gestión de Prácticas Profesionales v2.0**  
Universidad Peruana Unión  
Última actualización: Octubre 2025
