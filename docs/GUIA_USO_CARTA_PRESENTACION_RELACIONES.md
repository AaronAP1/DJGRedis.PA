# 📋 Guía de Uso: Carta de Presentación con Relaciones

## 🎯 Cambios Implementados

Se han agregado **relaciones mediante ForeignKeys** al modelo `PresentationLetterRequest`:

1. ✅ **Escuela Profesional** → `ForeignKey` a `School`
2. ✅ **Empresa** → `ForeignKey` a `Company`
3. ✅ **Auto-rellenado** de campos de texto desde las relaciones
4. ✅ **Migración de datos** existentes

---

## 📡 Endpoints Disponibles

### 1. Listar Escuelas Activas

```http
GET /api/v2/schools/
```

**Response:**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "nombre": "Ingeniería de Sistemas",
      "codigo": "EP-IS",
      "estado": "ACTIVO"
    },
    {
      "id": 2,
      "nombre": "Ingeniería Civil",
      "codigo": "EP-IC",
      "estado": "ACTIVO"
    }
  ]
}
```

---

### 2. Listar Empresas Activas

```http
GET /api/v2/companies/?estado=ACTIVO
```

**Query Parameters:**
- `search`: Buscar por nombre, RUC o razón social
- `estado`: Filtrar por estado (ACTIVO, PENDIENTE)
- `sector_economico`: Filtrar por sector

**Response:**
```json
{
  "count": 10,
  "results": [
    {
      "id": 5,
      "nombre": "Tech Solutions SAC",
      "ruc": "20123456789",
      "razon_social": "Tech Solutions Sociedad Anónima Cerrada",
      "direccion": "Av. Ejemplo 123, Lima",
      "telefono": "01-9876543",
      "correo": "contacto@techsolutions.com",
      "sector_economico": "Tecnología",
      "estado": "ACTIVO"
    }
  ]
}
```

---

### 3. Buscar Empresa por RUC

```http
GET /api/v2/companies/search-by-ruc/?ruc=20123456789
```

**Response (encontrada):**
```json
{
  "found": true,
  "data": {
    "id": 5,
    "nombre": "Tech Solutions SAC",
    "ruc": "20123456789",
    ...
  }
}
```

**Response (no encontrada):**
```json
{
  "found": false,
  "message": "No se encontró empresa con RUC 20123456789"
}
```

---

### 4. Crear Nueva Empresa

```http
POST /api/v2/companies/
Content-Type: application/json
```

**Request Body:**
```json
{
  "nombre": "Nueva Empresa SAC",
  "ruc": "20987654321",
  "razon_social": "Nueva Empresa Sociedad Anónima Cerrada",
  "direccion": "Av. Nueva 456, Lima",
  "distrito": "Lima",
  "provincia": "Lima",
  "departamento": "Lima",
  "telefono": "01-5551234",
  "correo": "info@nuevaempresa.com",
  "sector_economico": "Tecnología",
  "tamaño_empresa": "PEQUEÑA"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Empresa creada exitosamente en estado PENDIENTE",
  "data": {
    "id": 15,
    "nombre": "Nueva Empresa SAC",
    "ruc": "20987654321",
    "estado": "PENDIENTE",
    ...
  }
}
```

---

### 5. Crear Solicitud de Carta de Presentación

#### Opción A: Con Empresa Existente

```http
POST /api/v2/cartas-presentacion/
Content-Type: application/json
Authorization: Bearer {jwt_token}
```

**Request Body:**
```json
{
  "escuela_id": 1,
  "empresa_id": 5,
  "year_of_study": "Quinto año",
  "study_cycle": "IX",
  "company_representative": "Juan Pérez García",
  "company_position": "Gerente de Recursos Humanos",
  "company_phone": "01-2345678",
  "practice_area": "Desarrollo de Software",
  "start_date": "2025-03-01"
}
```

**Response:**
```json
{
  "id": 1,
  "escuela_id": 1,
  "empresa_id": 5,
  "ep": "Ingeniería de Sistemas",
  "student_full_name": "María García López",
  "student_code": "2020123456",
  "student_email": "maria.garcia@upeu.edu.pe",
  "year_of_study": "Quinto año",
  "study_cycle": "IX",
  "company_name": "Tech Solutions SAC",
  "company_address": "Av. Ejemplo 123, Lima",
  "company_representative": "Juan Pérez García",
  "company_position": "Gerente de Recursos Humanos",
  "company_phone": "01-2345678",
  "practice_area": "Desarrollo de Software",
  "start_date": "2025-03-01",
  "status": "DRAFT",
  "created_at": "2025-11-02T10:00:00Z"
}
```

#### Opción B: Sin Empresa (Datos Manuales)

```json
{
  "year_of_study": "Quinto año",
  "study_cycle": "IX",
  "company_name": "Empresa Nueva",
  "company_representative": "Pedro Sánchez",
  "company_position": "Director",
  "company_phone": "01-9999999",
  "company_address": "Calle Falsa 123",
  "practice_area": "Redes",
  "start_date": "2025-03-01"
}
```

**Nota:** Si no se proporciona `empresa_id`, debe proporcionar `company_name` manualmente.

---

### 6. Ver Detalle de Solicitud (con Relaciones Expandidas)

```http
GET /api/v2/cartas-presentacion/{id}/
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "id": 1,
  "student": 5,
  "escuela": 1,
  "empresa": 5,
  "assigned_secretary": null,
  
  "student_info": {
    "id": 5,
    "codigo": "2020123456",
    "nombres": "María",
    "apellidos": "García López",
    "email": "maria.garcia@upeu.edu.pe"
  },
  
  "escuela_info": {
    "id": 1,
    "nombre": "Ingeniería de Sistemas",
    "codigo": "EP-IS"
  },
  
  "empresa_info": {
    "id": 5,
    "nombre": "Tech Solutions SAC",
    "ruc": "20123456789",
    "razon_social": "Tech Solutions Sociedad Anónima Cerrada",
    "direccion": "Av. Ejemplo 123, Lima",
    "telefono": "01-9876543",
    "correo": "contacto@techsolutions.com",
    "sector_economico": "Tecnología"
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
  
  "created_at": "2025-11-02T10:00:00Z",
  "updated_at": "2025-11-02T10:00:00Z",
  "submitted_at": null,
  "reviewed_at": null
}
```

---

## 🔄 Flujo Completo de Uso

### Paso 1: Estudiante Busca Empresa

```javascript
// 1. Buscar empresa por RUC
const response = await fetch('/api/v2/companies/search-by-ruc/?ruc=20123456789');
const { found, data } = await response.json();

if (found) {
  console.log('Empresa encontrada:', data.nombre);
  // Usar empresa_id en el formulario
} else {
  console.log('Empresa no encontrada - crear nueva');
  // Mostrar formulario para crear empresa
}
```

### Paso 2: (Opcional) Crear Empresa Nueva

```javascript
// Si la empresa no existe, crearla
const newCompany = await fetch('/api/v2/companies/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    nombre: 'Nueva Empresa SAC',
    ruc: '20987654321',
    razon_social: 'Nueva Empresa SAC',
    direccion: 'Av. Nueva 456',
    telefono: '01-5551234',
    correo: 'info@nueva.com',
    sector_economico: 'Tecnología'
  })
});

const { data } = await newCompany.json();
const empresaId = data.id;
```

### Paso 3: Crear Solicitud de Carta

```javascript
// Crear solicitud con empresa_id
const solicitud = await fetch('/api/v2/cartas-presentacion/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    escuela_id: 1,  // Auto-seleccionada desde perfil
    empresa_id: empresaId,  // ID de la empresa
    year_of_study: 'Quinto año',
    study_cycle: 'IX',
    company_representative: 'Juan Pérez',
    company_position: 'Gerente RRHH',
    company_phone: '01-2345678',
    practice_area: 'Desarrollo Software',
    start_date: '2025-03-01'
  })
});

const carta = await solicitud.json();
console.log('Carta creada:', carta.id);
```

---

## 📊 Ventajas de las Relaciones

### 1. Auto-completado Inteligente

```javascript
// Al seleccionar empresa_id, se auto-completan:
{
  "empresa_id": 5,
  // Estos campos se llenan automáticamente:
  "company_name": "Tech Solutions SAC",  // ← Auto
  "company_address": "Av. Ejemplo 123"   // ← Auto
}
```

### 2. Validación de Datos

```javascript
// Intenta crear con empresa que no existe
{
  "empresa_id": 999  // ← Error: empresa no existe
}

// Respuesta:
{
  "empresa_id": ["Invalid pk '999' - object does not exist."]
}
```

### 3. Consultas Relacionadas

```python
# Backend: Obtener todas las cartas de una empresa
cartas = PresentationLetterRequest.objects.filter(empresa_id=5)

# Obtener top empresas
top_empresas = (
    PresentationLetterRequest.objects
    .filter(empresa__isnull=False)
    .values('empresa__nombre')
    .annotate(total=Count('id'))
    .order_by('-total')
)
```

---

## 🔧 Migración de Datos Existentes

Para migrar datos existentes, ejecutar:

```bash
# Aplicar migración
python manage.py migrate

# Ejecutar script de migración de datos
python scripts/migrate_presentation_letter_data.py
```

El script:
1. ✅ Asigna `escuela` desde `StudentProfile.escuela`
2. ✅ Busca `empresa` por nombre (si existe)
3. ✅ Auto-completa campos de texto
4. 📊 Genera reporte de migración

---

## 📝 Notas Importantes

### Campos Obligatorios vs Opcionales

| Campo | ¿Obligatorio? | Notas |
|-------|---------------|-------|
| `escuela_id` | ⚠️ Opcional | Se auto-asigna desde `StudentProfile.escuela` |
| `empresa_id` | ❌ Opcional | Si no se proporciona, usar `company_name` manual |
| `company_name` | ✅ Si no hay `empresa_id` | Se auto-rellena si hay `empresa_id` |
| `company_address` | ✅ Si no hay `empresa_id` | Se auto-rellena si hay `empresa_id` |
| `company_representative` | ✅ Siempre | Específico de la carta |
| `company_position` | ✅ Siempre | Específico de la carta |
| `company_phone` | ✅ Siempre | Puede ser diferente al de la empresa |

### Campos Auto-rellenados

Estos campos se llenan **automáticamente** al guardar:

```python
# Desde el estudiante autenticado:
- student_full_name
- student_code
- student_email
- escuela (desde StudentProfile.escuela)
- ep (desde escuela.nombre)

# Si se proporciona empresa_id:
- company_name (desde empresa.nombre)
- company_address (desde empresa.direccion)
```

---

## 🚀 Ejemplos de Frontend

### React/Vue/Angular

```jsx
// Componente de formulario
const [escuelas, setEscuelas] = useState([]);
const [empresas, setEmpresas] = useState([]);
const [empresaSeleccionada, setEmpresaSeleccionada] = useState(null);

// Cargar escuelas y empresas al montar
useEffect(() => {
  fetch('/api/v2/schools/')
    .then(r => r.json())
    .then(data => setEscuelas(data.results));
  
  fetch('/api/v2/companies/?estado=ACTIVO')
    .then(r => r.json())
    .then(data => setEmpresas(data.results));
}, []);

// Al seleccionar empresa, auto-completar campos
const handleEmpresaChange = (empresaId) => {
  const empresa = empresas.find(e => e.id === empresaId);
  if (empresa) {
    setEmpresaSeleccionada(empresa);
    // Auto-llenar formulario
    setFormData(prev => ({
      ...prev,
      empresa_id: empresa.id,
      // Estos se muestran readonly
      company_name: empresa.nombre,
      company_address: empresa.direccion
    }));
  }
};

// Formulario
<form onSubmit={handleSubmit}>
  {/* Escuela (auto-seleccionada, mostrar readonly) */}
  <input 
    type="text" 
    value={formData.ep} 
    readOnly 
    disabled
  />
  
  {/* Empresa (select con búsqueda) */}
  <select onChange={(e) => handleEmpresaChange(e.target.value)}>
    <option value="">Nueva empresa (ingresar datos)</option>
    {empresas.map(emp => (
      <option key={emp.id} value={emp.id}>
        {emp.nombre} - RUC: {emp.ruc}
      </option>
    ))}
  </select>
  
  {/* Si seleccionó empresa, mostrar datos readonly */}
  {empresaSeleccionada && (
    <>
      <input 
        value={empresaSeleccionada.nombre} 
        readOnly 
      />
      <textarea 
        value={empresaSeleccionada.direccion} 
        readOnly 
      />
    </>
  )}
  
  {/* Campos editables siempre */}
  <input 
    name="company_representative"
    placeholder="Nombre del representante"
    required
  />
  <input 
    name="company_position"
    placeholder="Cargo"
    required
  />
  <input 
    name="company_phone"
    placeholder="Teléfono de contacto"
    required
  />
</form>
```

---

## 📚 Recursos Adicionales

- **Documentación completa**: Ver `docs/ANALISIS_CARTA_PRESENTACION_RELACIONES.md`
- **Swagger**: `/api/docs/`
- **Scalar**: `/api/scalar/`

---

**Fecha:** 2025-11-02  
**Versión:** 2.0  
**Estado:** Implementado ✅
