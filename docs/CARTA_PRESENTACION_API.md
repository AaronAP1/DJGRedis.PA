# 📋 API de Solicitud de Carta de Presentación

## ✅ Implementación Completada

Se ha implementado exitosamente el módulo de **Solicitud de Carta de Presentación** como primer paso del proceso de prácticas profesionales.

---

## 🎯 Descripción

Este módulo permite a los estudiantes solicitar una carta de presentación oficial de la universidad para presentar ante empresas donde desean realizar sus prácticas profesionales.

### Flujo del Proceso

```
1. PRACTICANTE crea solicitud → Estado: DRAFT
2. PRACTICANTE envía a secretaría → Estado: PENDING
3. SECRETARIA revisa y aprueba → Estado: APPROVED
4. SECRETARIA genera PDF → Estado: GENERATED
5. PRACTICANTE descarga carta
6. (Opcional) PRACTICANTE usa carta para crear práctica → Estado: USED
```

---

## 📊 Modelo de Datos

### Tabla: `presentation_letter_requests`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | INTEGER | Primary Key |
| `student_id` | FK | Referencia a StudentProfile |
| `assigned_secretary_id` | FK | Secretaria que procesó |
| **Datos del Estudiante** | | |
| `ep` | VARCHAR(200) | Escuela Profesional |
| `student_full_name` | VARCHAR(200) | Nombre completo |
| `student_code` | VARCHAR(20) | Código estudiante |
| `year_of_study` | VARCHAR(50) | Año de estudios |
| `study_cycle` | VARCHAR(10) | Ciclo (IX, X, etc.) |
| `student_email` | EMAIL | Email del estudiante |
| **Datos de la Empresa** | | |
| `company_name` | VARCHAR(255) | Nombre empresa |
| `company_representative` | VARCHAR(200) | Representante |
| `company_position` | VARCHAR(100) | Cargo/Grado académico |
| `company_phone` | VARCHAR(50) | Teléfono - Fax |
| `company_address` | TEXT | Dirección |
| `practice_area` | VARCHAR(100) | Área de práctica |
| **Control** | | |
| `start_date` | DATE | Fecha inicio tentativa |
| `status` | VARCHAR(20) | Estado actual |
| `letter_document_id` | FK | PDF generado |
| `rejection_reason` | TEXT | Motivo rechazo |
| `created_at` | TIMESTAMP | Fecha creación |
| `updated_at` | TIMESTAMP | Última actualización |
| `submitted_at` | TIMESTAMP | Fecha envío |
| `reviewed_at` | TIMESTAMP | Fecha revisión |

### Estados Disponibles

| Estado | Descripción | Siguiente Estado |
|--------|-------------|------------------|
| `DRAFT` | Borrador (estudiante editando) | `PENDING` |
| `PENDING` | Enviado a secretaría | `APPROVED`, `REJECTED` |
| `APPROVED` | Aprobado por secretaria | `GENERATED` |
| `REJECTED` | Rechazado (debe corregir) | `DRAFT` |
| `GENERATED` | PDF de carta generado | `USED` |
| `USED` | Usada para crear práctica | - |

---

## 🚀 Endpoints REST API

### Base URL
```
/api/v2/presentation-letters/
```

### 1. Crear Solicitud (PRACTICANTE)

**POST** `/api/v2/presentation-letters/`

**Request Body:**
```json
{
  "year_of_study": "Quinto año",
  "study_cycle": "IX",
  "company_name": "Tech Solutions SAC",
  "company_representative": "Juan Pérez García",
  "company_position": "Gerente de Recursos Humanos",
  "company_phone": "01-2345678",
  "company_address": "Av. Ejemplo 123, Lima",
  "practice_area": "Desarrollo de Software",
  "start_date": "2025-03-01"
}
```

**Response:** (Estado: `DRAFT`)
```json
{
  "id": 1,
  "ep": "Ingeniería de Sistemas",
  "student_full_name": "María García López",
  "student_code": "2020123456",
  "student_email": "maria.garcia@upeu.edu.pe",
  "year_of_study": "Quinto año",
  "study_cycle": "IX",
  "company_name": "Tech Solutions SAC",
  "company_representative": "Juan Pérez García",
  "company_position": "Gerente de Recursos Humanos",
  "company_phone": "01-2345678",
  "company_address": "Av. Ejemplo 123, Lima",
  "practice_area": "Desarrollo de Software",
  "start_date": "2025-03-01",
  "status": "DRAFT",
  "created_at": "2025-10-31T10:00:00Z",
  "updated_at": "2025-10-31T10:00:00Z"
}
```

---

### 2. Listar Solicitudes

**GET** `/api/v2/presentation-letters/`

**Query Parameters:**
- `status`: Filtrar por estado
- `search`: Buscar por código, nombre o empresa

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "student_code": "2020123456",
      "student_name": "María García López",
      "company_name": "Tech Solutions SAC",
      "practice_area": "Desarrollo de Software",
      "start_date": "2025-03-01",
      "status": "DRAFT",
      "status_display": "Borrador",
      "secretary_name": null,
      "created_at": "2025-10-31T10:00:00Z",
      "submitted_at": null,
      "reviewed_at": null
    }
  ]
}
```

---

### 3. Ver Detalle de Solicitud

**GET** `/api/v2/presentation-letters/{id}/`

**Response:**
```json
{
  "id": 1,
  "student_info": {
    "id": 5,
    "codigo": "2020123456",
    "nombres": "María",
    "apellidos": "García López",
    "email": "maria.garcia@upeu.edu.pe"
  },
  "secretary_info": null,
  "ep": "Ingeniería de Sistemas",
  "student_full_name": "María García López",
  "student_code": "2020123456",
  "student_email": "maria.garcia@upeu.edu.pe",
  "year_of_study": "Quinto año",
  "study_cycle": "IX",
  "company_name": "Tech Solutions SAC",
  "company_representative": "Juan Pérez García",
  "company_position": "Gerente de Recursos Humanos",
  "company_phone": "01-2345678",
  "company_address": "Av. Ejemplo 123, Lima",
  "practice_area": "Desarrollo de Software",
  "start_date": "2025-03-01",
  "status": "DRAFT",
  "letter_document": null,
  "letter_document_url": null,
  "rejection_reason": null,
  "created_at": "2025-10-31T10:00:00Z",
  "updated_at": "2025-10-31T10:00:00Z",
  "submitted_at": null,
  "reviewed_at": null
}
```

---

### 4. Actualizar Solicitud (PRACTICANTE - solo DRAFT/REJECTED)

**PUT/PATCH** `/api/v2/presentation-letters/{id}/`

**Request Body:** (campos a actualizar)
```json
{
  "company_phone": "01-9876543",
  "practice_area": "Backend Development"
}
```

---

### 5. Enviar a Secretaría (PRACTICANTE)

**POST** `/api/v2/presentation-letters/{id}/submit/`

**Response:**
```json
{
  "success": true,
  "message": "Solicitud enviada a secretaría exitosamente",
  "data": {
    "id": 1,
    "status": "PENDING",
    "submitted_at": "2025-10-31T10:15:00Z"
  }
}
```

---

### 6. Aprobar Solicitud (SECRETARIA)

**POST** `/api/v2/presentation-letters/{id}/approve/`

**Response:**
```json
{
  "success": true,
  "message": "Solicitud aprobada exitosamente",
  "data": {
    "id": 1,
    "status": "APPROVED",
    "assigned_secretary": 3,
    "reviewed_at": "2025-10-31T11:00:00Z"
  }
}
```

---

### 7. Rechazar Solicitud (SECRETARIA)

**POST** `/api/v2/presentation-letters/{id}/reject/`

**Request Body:**
```json
{
  "rejection_reason": "Los datos de la empresa están incompletos. Por favor verifica el RUC y la dirección completa."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Solicitud rechazada",
  "data": {
    "id": 1,
    "status": "REJECTED",
    "rejection_reason": "Los datos de la empresa están incompletos...",
    "reviewed_at": "2025-10-31T11:00:00Z"
  }
}
```

---

### 8. Generar PDF (SECRETARIA)

**POST** `/api/v2/presentation-letters/{id}/generate-pdf/`

**Response:**
```json
{
  "success": true,
  "message": "Carta de presentación generada exitosamente",
  "document_id": 15,
  "download_url": "https://upeu-ppp-api-5983.azurewebsites.net/media/documents/carta_presentacion_2020123456_20251031.pdf"
}
```

---

### 9. Descargar Carta (TODOS)

**GET** `/api/v2/presentation-letters/{id}/download/`

**Response:**
```json
{
  "success": true,
  "download_url": "https://upeu-ppp-api-5983.azurewebsites.net/media/documents/carta_presentacion_2020123456_20251031.pdf",
  "document_id": 15,
  "filename": "carta_presentacion_2020123456_20251031.pdf"
}
```

---

### 10. Eliminar Solicitud (PRACTICANTE - solo DRAFT)

**DELETE** `/api/v2/presentation-letters/{id}/`

**Response:** `204 No Content`

---

## 🎨 Ejemplo de Uso Frontend

### JavaScript Vanilla

```javascript
// 1. Crear solicitud
const crearSolicitud = async () => {
  const response = await fetch(
    'https://upeu-ppp-api-5983.azurewebsites.net/api/v2/presentation-letters/',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        year_of_study: "Quinto año",
        study_cycle: "IX",
        company_name: "Tech Solutions SAC",
        company_representative: "Juan Pérez García",
        company_position: "Gerente de Recursos Humanos",
        company_phone: "01-2345678",
        company_address: "Av. Ejemplo 123, Lima",
        practice_area: "Desarrollo de Software",
        start_date: "2025-03-01"
      })
    }
  );
  
  const data = await response.json();
  console.log('Solicitud creada:', data);
  // Estado: DRAFT
};

// 2. Enviar a secretaría
const enviarASecretaria = async (id) => {
  const response = await fetch(
    `https://upeu-ppp-api-5983.azurewebsites.net/api/v2/presentation-letters/${id}/submit/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  
  const data = await response.json();
  console.log('Enviado:', data);
  // Estado: PENDING
};

// 3. Secretaria aprueba
const aprobar = async (id) => {
  const response = await fetch(
    `https://upeu-ppp-api-5983.azurewebsites.net/api/v2/presentation-letters/${id}/approve/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${secretariaToken}`
      }
    }
  );
  
  const data = await response.json();
  console.log('Aprobado:', data);
  // Estado: APPROVED
};

// 4. Secretaria genera PDF
const generarPDF = async (id) => {
  const response = await fetch(
    `https://upeu-ppp-api-5983.azurewebsites.net/api/v2/presentation-letters/${id}/generate-pdf/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${secretariaToken}`
      }
    }
  );
  
  const data = await response.json();
  console.log('PDF generado:', data);
  // Estado: GENERATED
  // data.download_url contiene la URL del PDF
};

// 5. Estudiante descarga carta
const descargarCarta = async (id) => {
  const response = await fetch(
    `https://upeu-ppp-api-5983.azurewebsites.net/api/v2/presentation-letters/${id}/download/`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  
  const data = await response.json();
  
  // Abrir en nueva ventana o descargar
  window.open(data.download_url, '_blank');
};
```

---

## 🔐 Permisos por Rol

| Acción | PRACTICANTE | SECRETARIA | COORDINADOR | ADMIN |
|--------|-------------|------------|-------------|-------|
| Crear solicitud | ✅ | ❌ | ❌ | ❌ |
| Ver propias solicitudes | ✅ | ❌ | ❌ | ❌ |
| Editar (DRAFT/REJECTED) | ✅ | ❌ | ❌ | ❌ |
| Enviar a secretaría | ✅ | ❌ | ❌ | ❌ |
| Ver asignadas/pendientes | ❌ | ✅ | ❌ | ❌ |
| Aprobar | ❌ | ✅ | ❌ | ❌ |
| Rechazar | ❌ | ✅ | ❌ | ❌ |
| Generar PDF | ❌ | ✅ | ❌ | ❌ |
| Descargar carta | ✅ | ✅ | ✅ | ✅ |
| Ver todas | ❌ | ❌ | ✅ | ✅ |

---

## 📄 Contenido del PDF Generado

El PDF incluye:

1. **Membrete**: Logo y datos de la Universidad Peruana Unión
2. **Fecha**: Fecha de generación
3. **Destinatario**: Nombre, cargo y empresa
4. **Asunto**: CARTA DE PRESENTACIÓN
5. **Cuerpo**:
   - Presentación del estudiante
   - Año y ciclo de estudios
   - Área de práctica solicitada
   - Fecha tentativa de inicio
   - Propósito de las prácticas
6. **Firma**: Espacio para firma del Coordinador
7. **Datos de contacto**: Email del estudiante y teléfono de la empresa

---

## 🧪 Testing con Swagger/Scalar

### Acceder a la documentación:
- **Scalar UI**: https://upeu-ppp-api-5983.azurewebsites.net/api/docs/
- **Swagger UI**: https://upeu-ppp-api-5983.azurewebsites.net/api/swagger/

### Pasos para probar:

1. **Autenticarse**:
   - POST `/api/v2/auth/login/`
   - Copiar el `access_token`
   - Click en "Authorize" y pegar token

2. **Crear solicitud** (como PRACTICANTE):
   - POST `/api/v2/presentation-letters/`
   - Rellenar datos del formulario

3. **Enviar a secretaría**:
   - POST `/api/v2/presentation-letters/{id}/submit/`

4. **Aprobar** (como SECRETARIA):
   - Autenticarse con cuenta de secretaria
   - POST `/api/v2/presentation-letters/{id}/approve/`

5. **Generar PDF**:
   - POST `/api/v2/presentation-letters/{id}/generate-pdf/`

6. **Descargar**:
   - GET `/api/v2/presentation-letters/{id}/download/`

---

## 📊 Archivos Implementados

```
src/
├── domain/
│   └── enums.py                          # ✅ Agregado PresentationLetterStatus
│
├── adapters/
│   ├── secondary/
│   │   └── database/
│   │       ├── models.py                 # ✅ Modelo PresentationLetterRequest
│   │       └── migrations/
│   │           └── 0016_add_presentation_letter_request.py
│   │
│   └── primary/
│       └── rest_api/
│           ├── presentation_letter_serializers.py    # ✅ Nuevo
│           ├── presentation_letter_viewset.py        # ✅ Nuevo
│           └── urls_api_v2.py            # ✅ Modificado (router)
│
└── application/
    └── services/
        └── pdf_generator.py              # ✅ Nuevo (genera PDF)
```

---

## ✅ Checklist de Implementación

- [x] Modelo `PresentationLetterRequest` creado
- [x] Enum `PresentationLetterStatus` agregado
- [x] Serializers implementados
- [x] ViewSet con todas las acciones
- [x] Endpoints registrados en URLs
- [x] Servicio de generación de PDF
- [x] Migración de base de datos aplicada
- [x] Permisos por rol configurados
- [x] Validaciones implementadas
- [x] Documentación API generada

---

## 🚀 Próximos Pasos

1. ✅ **Testing**: Crear tests unitarios y de integración
2. ✅ **Notificaciones**: Implementar notificaciones por email
3. ✅ **Template PDF**: Mejorar diseño del PDF con logo oficial
4. ✅ **Dashboard**: Agregar estadísticas de cartas en dashboard
5. ✅ **Frontend**: Integrar formulario en React/Vue

---

## 📞 Soporte

Para dudas o problemas:
- **Documentación Swagger**: `/api/docs/`
- **Logs del servidor**: Revisar `logs/` directory
- **Errores comunes**: Ver sección de troubleshooting

---

**Fecha de implementación**: 31 de Octubre, 2025  
**Versión**: 1.0.0  
**Estado**: ✅ Implementado y funcionando
