# 📊 Dashboards y Reportes - Fase 7

Endpoints especializados para dashboards personalizados por rol, reportes estadísticos y exportación de datos.

---

## 📦 Módulos Implementados

### 1. **DashboardViewSet** (`dashboards.py`)
- Dashboards personalizados por rol
- Estadísticas en tiempo real
- Métricas y KPIs
- Datos para gráficas

### 2. **ReportsViewSet** (`reports.py`)
- Reportes con filtros avanzados
- Exportación Excel/CSV
- Certificados de prácticas
- Resúmenes estadísticos

---

## 🎯 Endpoints Dashboard

Base URL: `/api/v2/dashboards/`

### 1. Dashboard General (Coordinador/Administrador)

```http
GET /api/v2/dashboards/general/
```

**Requiere**: `COORDINADOR` o `ADMINISTRADOR`

**Response**:
```json
{
  "success": true,
  "data": {
    "practices": {
      "total": 150,
      "by_status": {
        "PENDING": 12,
        "APPROVED": 5,
        "IN_PROGRESS": 45,
        "COMPLETED": 88
      },
      "pending_approval": 12,
      "in_progress": 45,
      "completed": 88
    },
    "students": {
      "total": 500,
      "eligible": 350,
      "with_practice": 150,
      "without_practice": 350
    },
    "companies": {
      "total": 75,
      "validated": 68,
      "active": 65,
      "by_sector": [
        {"sector_economico": "Tecnología", "count": 25},
        {"sector_economico": "Finanzas", "count": 15}
      ]
    },
    "documents": {
      "total": 500,
      "by_status": {
        "PENDING": 25,
        "APPROVED": 450,
        "REJECTED": 25
      },
      "pending_approval": 25
    },
    "notifications": {
      "unread_count": 15
    },
    "recent_activities": [
      {
        "type": "practice",
        "action": "created",
        "description": "Nueva práctica: Desarrollo Web",
        "user": "Juan Pérez",
        "timestamp": "2024-10-15T10:30:00Z"
      }
    ],
    "generated_at": "2024-10-17T14:30:00Z"
  }
}
```

**Características**:
- Vista completa del sistema
- Estadísticas de todas las entidades
- Actividades recientes
- Notificaciones pendientes

---

### 2. Dashboard Estudiante

```http
GET /api/v2/dashboards/student/
```

**Requiere**: `PRACTICANTE` (estudiante autenticado)

**Response**:
```json
{
  "success": true,
  "data": {
    "profile": {
      "codigo": "2024012345",
      "carrera": "Ingeniería de Sistemas",
      "semestre": 7,
      "promedio": 15.5,
      "estado": "ACTIVE",
      "elegible_practicas": true
    },
    "current_practice": {
      "id": 25,
      "titulo": "Desarrollo de Sistema Web",
      "company": {
        "id": 10,
        "razon_social": "TechCorp SAC"
      },
      "supervisor": {
        "id": 5,
        "nombre": "María González"
      },
      "estado": "IN_PROGRESS",
      "fecha_inicio": "2024-03-01",
      "fecha_fin": "2024-08-31",
      "horas_totales": 640,
      "horas_completadas": 320
    },
    "practice_progress": {
      "horas_completadas": 320,
      "horas_totales": 640,
      "horas_restantes": 320,
      "porcentaje_completado": 50.0
    },
    "pending_documents": 2,
    "notifications": {
      "unread_count": 5,
      "recent": [
        {
          "id": 101,
          "tipo": "PRACTICE_UPDATED",
          "mensaje": "Tu práctica ha sido aprobada",
          "created_at": "2024-10-15T09:00:00Z"
        }
      ]
    },
    "hours_summary": {
      "by_month": [
        {"month": "2024-03", "horas": 80},
        {"month": "2024-04", "horas": 80},
        {"month": "2024-05", "horas": 80},
        {"month": "2024-06", "horas": 80}
      ],
      "promedio_semanal": 20.0
    },
    "generated_at": "2024-10-17T14:30:00Z"
  }
}
```

**Características**:
- Información del perfil académico
- Práctica actual en progreso
- Progreso detallado con porcentajes
- Documentos pendientes
- Resumen de horas por mes
- Notificaciones no leídas

---

### 3. Dashboard Supervisor

```http
GET /api/v2/dashboards/supervisor/
```

**Requiere**: `SUPERVISOR` (supervisor autenticado)

**Response**:
```json
{
  "success": true,
  "data": {
    "profile": {
      "nombre": "María González",
      "cargo": "Jefe de Desarrollo",
      "email": "maria@techcorp.com",
      "telefono": "987654321",
      "company": {
        "id": 10,
        "razon_social": "TechCorp SAC",
        "sector": "Tecnología"
      }
    },
    "practices_statistics": {
      "total": 15,
      "by_status": {
        "PENDING": 2,
        "IN_PROGRESS": 8,
        "COMPLETED": 5
      }
    },
    "active_practices": [
      {
        "id": 25,
        "titulo": "Desarrollo Web",
        "student": {
          "id": 50,
          "nombre": "Juan Pérez",
          "codigo": "2024012345"
        },
        "fecha_inicio": "2024-03-01",
        "horas_completadas": 320,
        "horas_totales": 640,
        "progreso": 50.0
      }
    ],
    "pending_evaluations": 5,
    "students_performance": [
      {
        "student_name": "Juan Pérez",
        "practice_title": "Desarrollo Web",
        "progress": 50.0,
        "status": "IN_PROGRESS"
      }
    ],
    "generated_at": "2024-10-17T14:30:00Z"
  }
}
```

**Características**:
- Información del perfil y empresa
- Estadísticas de prácticas asignadas
- Lista de prácticas activas
- Evaluaciones pendientes
- Rendimiento de estudiantes

---

### 4. Dashboard Secretaría

```http
GET /api/v2/dashboards/secretary/
```

**Requiere**: `SECRETARIA`

**Response**:
```json
{
  "success": true,
  "data": {
    "pending_validations": {
      "companies": 8,
      "documents": 15,
      "practices": 10,
      "total": 33
    },
    "recent_registrations": {
      "students": 25,
      "companies": 3,
      "practices": 12,
      "period": "7 days"
    },
    "documents_status": {
      "PENDING": 15,
      "APPROVED": 250,
      "REJECTED": 10
    },
    "companies_to_validate": [
      {
        "id": 20,
        "razon_social": "Nueva Empresa SAC",
        "ruc": "20123456789",
        "sector": "Comercio",
        "fecha_registro": "2024-10-15"
      }
    ],
    "generated_at": "2024-10-17T14:30:00Z"
  }
}
```

**Características**:
- Validaciones pendientes (empresas, documentos, prácticas)
- Registros recientes (últimos 7 días)
- Estado de documentos
- Lista de empresas pendientes de validar

---

### 5. Estadísticas Completas

```http
GET /api/v2/dashboards/statistics/
    ?period=month|quarter|year
    &start_date=2024-01-01
    &end_date=2024-12-31
```

**Requiere**: `COORDINADOR` o `ADMINISTRADOR`

**Parámetros**:
- `period`: Período de análisis (`month`, `quarter`, `year`)
- `start_date`: Fecha inicio (YYYY-MM-DD)
- `end_date`: Fecha fin (YYYY-MM-DD)

**Response**:
```json
{
  "success": true,
  "data": {
    "period": {
      "type": "month",
      "start": "2024-09-17T00:00:00Z",
      "end": "2024-10-17T00:00:00Z"
    },
    "practices_timeline": [
      {"period": "2024-09", "count": 25},
      {"period": "2024-10", "count": 18}
    ],
    "students_by_career": [
      {"career": "Ingeniería de Sistemas", "count": 200},
      {"career": "Administración", "count": 150}
    ],
    "companies_by_sector": [
      {"sector": "Tecnología", "count": 25},
      {"sector": "Finanzas", "count": 15}
    ],
    "completion_rate": 85.5,
    "average_hours": 580.0,
    "average_satisfaction": 4.2,
    "generated_at": "2024-10-17T14:30:00Z"
  }
}
```

**Características**:
- Línea temporal de prácticas
- Distribución por carreras
- Distribución por sectores
- Tasas de completación
- Promedios de horas y satisfacción

---

### 6. Datos para Gráficas

```http
GET /api/v2/dashboards/charts/
    ?type=practices_status|students_career|companies_sector|practices_timeline
```

**Requiere**: Autenticado

**Parámetros**:
- `type`: Tipo de gráfica
  - `practices_status`: Estado de prácticas (pie chart)
  - `students_career`: Estudiantes por carrera (bar chart)
  - `companies_sector`: Empresas por sector (bar chart)
  - `practices_timeline`: Línea temporal (line chart)

**Response** (ejemplo `practices_status`):
```json
{
  "success": true,
  "chart_type": "practices_status",
  "data": {
    "labels": ["PENDING", "IN_PROGRESS", "COMPLETED"],
    "datasets": [{
      "data": [12, 45, 88],
      "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56"]
    }]
  }
}
```

**Formatos soportados**:
- Chart.js
- Recharts
- Victory Charts
- Compatible con la mayoría de librerías

---

## 📄 Endpoints Reportes

Base URL: `/api/v2/reports/`

### 1. Reporte de Prácticas

```http
GET /api/v2/reports/practices/
    ?status=IN_PROGRESS,COMPLETED
    &start_date=2024-01-01
    &end_date=2024-12-31
    &career=Ingeniería de Sistemas
    &company_id=10
    &format=json|excel|csv
```

**Requiere**: `COORDINADOR`, `ADMINISTRADOR` o `SECRETARIA`

**Parámetros**:
- `status`: Filtro por estado (múltiples valores separados por coma)
- `start_date`: Fecha inicio
- `end_date`: Fecha fin
- `career`: Carrera profesional
- `company_id`: ID de empresa
- `format`: Formato de salida (`json`, `excel`, `csv`)

**Response** (formato JSON):
```json
{
  "success": true,
  "count": 45,
  "data": [
    {
      "id": 25,
      "titulo": "Desarrollo Web",
      "estudiante": {
        "codigo": "2024012345",
        "nombre": "Juan Pérez",
        "carrera": "Ingeniería de Sistemas",
        "promedio": 15.5
      },
      "empresa": {
        "id": 10,
        "razon_social": "TechCorp SAC",
        "ruc": "20123456789",
        "sector": "Tecnología"
      },
      "supervisor": {
        "nombre": "María González",
        "cargo": "Jefe de Desarrollo"
      },
      "fechas": {
        "inicio": "2024-03-01",
        "fin": "2024-08-31",
        "registro": "2024-02-15"
      },
      "horas": {
        "totales": 640,
        "completadas": 320,
        "porcentaje": 50.0
      },
      "estado": "IN_PROGRESS",
      "modalidad": "PRESENCIAL"
    }
  ],
  "filters": {
    "status": ["IN_PROGRESS", "COMPLETED"],
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "career": "Ingeniería de Sistemas",
    "company_id": "10"
  },
  "generated_at": "2024-10-17T14:30:00Z"
}
```

**Exportación Excel**: Archivo `.xlsx` con formato profesional
**Exportación CSV**: Archivo `.csv` compatible con Excel

---

### 2. Reporte de Estudiantes

```http
GET /api/v2/reports/students/
    ?career=Ingeniería de Sistemas
    &semester=6,7,8
    &with_practice=true|false
    &format=json|excel|csv
```

**Requiere**: `COORDINADOR`, `ADMINISTRADOR` o `SECRETARIA`

**Parámetros**:
- `career`: Carrera profesional
- `semester`: Semestre(s) actual (múltiples valores)
- `with_practice`: Filtrar por presencia de práctica
- `format`: Formato de salida

**Response**:
```json
{
  "success": true,
  "count": 150,
  "data": [
    {
      "codigo": "2024012345",
      "nombre": "Juan Pérez",
      "email": "2024012345@upeu.edu.pe",
      "carrera": "Ingeniería de Sistemas",
      "semestre": 7,
      "promedio": 15.5,
      "elegible": true,
      "practica_actual": {
        "id": 25,
        "titulo": "Desarrollo Web",
        "empresa": "TechCorp SAC",
        "estado": "IN_PROGRESS"
      },
      "total_practicas": 1,
      "estado": "ACTIVE"
    }
  ],
  "generated_at": "2024-10-17T14:30:00Z"
}
```

---

### 3. Reporte de Empresas

```http
GET /api/v2/reports/companies/
    ?sector=Tecnología
    &validated=true|false
    &status=ACTIVE,SUSPENDED
    &format=json|excel|csv
```

**Requiere**: `COORDINADOR`, `ADMINISTRADOR` o `SECRETARIA`

**Response**:
```json
{
  "success": true,
  "count": 25,
  "data": [
    {
      "id": 10,
      "razon_social": "TechCorp SAC",
      "ruc": "20123456789",
      "sector": "Tecnología",
      "direccion": "Av. Ejemplo 123, Lima",
      "telefono": "987654321",
      "email": "contacto@techcorp.com",
      "validated": true,
      "estado": "ACTIVE",
      "fecha_registro": "2023-05-15",
      "estadisticas": {
        "total_practicas": 15,
        "practicas_activas": 8,
        "practicas_completadas": 7,
        "supervisores": 3
      }
    }
  ],
  "generated_at": "2024-10-17T14:30:00Z"
}
```

---

### 4. Resumen Estadístico

```http
GET /api/v2/reports/statistics_summary/
    ?format=json|pdf
```

**Requiere**: `COORDINADOR` o `ADMINISTRADOR`

**Response**:
```json
{
  "success": true,
  "data": {
    "practices": {
      "total": 150,
      "por_estado": {
        "PENDING": 12,
        "IN_PROGRESS": 45,
        "COMPLETED": 88
      },
      "completadas_mes": 15,
      "promedio_horas": 580.0
    },
    "students": {
      "total": 500,
      "elegibles": 350,
      "con_practica": 150,
      "por_carrera": [
        {"escuela_profesional": "Ingeniería de Sistemas", "count": 200}
      ]
    },
    "companies": {
      "total": 75,
      "validadas": 68,
      "activas": 65,
      "por_sector": [
        {"sector_economico": "Tecnología", "count": 25}
      ],
      "con_practicas_activas": 35
    },
    "documents": {
      "total": 500,
      "pendientes": 25,
      "aprobados": 450,
      "rechazados": 25
    },
    "users": {
      "total": 600,
      "activos": 580,
      "por_rol": {
        "PRACTICANTE": 500,
        "SUPERVISOR": 50,
        "COORDINADOR": 10,
        "SECRETARIA": 5,
        "ADMINISTRADOR": 2
      }
    },
    "trends": {
      "nuevas_practicas_mes": [
        {"month": 10, "count": 18}
      ],
      "nuevos_estudiantes_mes": [
        {"month": 10, "count": 25}
      ]
    },
    "generated_at": "2024-10-17T14:30:00Z"
  }
}
```

---

### 5. Certificado de Práctica

```http
GET /api/v2/reports/{practice_id}/certificate/
```

**Requiere**: Usuario relacionado a la práctica (estudiante, supervisor, coordinador, admin)

**Response**:
```json
{
  "success": true,
  "data": {
    "practice": {
      "id": 25,
      "titulo": "Desarrollo de Sistema Web",
      "modalidad": "PRESENCIAL",
      "fecha_inicio": "2024-03-01",
      "fecha_fin": "2024-08-31",
      "horas_totales": 640,
      "descripcion": "Desarrollo de aplicación web..."
    },
    "student": {
      "codigo": "2024012345",
      "nombre_completo": "Juan Pérez García",
      "carrera": "Ingeniería de Sistemas",
      "email": "2024012345@upeu.edu.pe"
    },
    "company": {
      "razon_social": "TechCorp SAC",
      "ruc": "20123456789",
      "sector": "Tecnología",
      "direccion": "Av. Ejemplo 123, Lima"
    },
    "supervisor": {
      "nombre": "María González",
      "cargo": "Jefe de Desarrollo",
      "email": "maria@techcorp.com"
    },
    "calificacion": 18.5,
    "observaciones": "Excelente desempeño...",
    "generated_at": "2024-10-17T14:30:00Z",
    "certificate_number": "CERT-000025-2024"
  }
}
```

**Nota**: La práctica debe estar en estado `COMPLETED`

---

## 🔐 Permisos por Endpoint

| Endpoint | ADMIN | COORD | SECRET | SUPER | ESTUD |
|----------|-------|-------|--------|-------|-------|
| `dashboards/general/` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `dashboards/student/` | ❌ | ❌ | ❌ | ❌ | ✅ |
| `dashboards/supervisor/` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `dashboards/secretary/` | ❌ | ❌ | ✅ | ❌ | ❌ |
| `dashboards/statistics/` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `dashboards/charts/` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `reports/practices/` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `reports/students/` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `reports/companies/` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `reports/statistics_summary/` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `reports/{id}/certificate/` | ✅ | ✅ | ❌ | ✅* | ✅* |

*Solo para prácticas relacionadas

---

## 📊 Ejemplos de Uso

### Dashboard Coordinador

```bash
curl -X GET "http://localhost:8000/api/v2/dashboards/general/" \
  -H "Authorization: Bearer <token>"
```

### Dashboard Estudiante

```bash
curl -X GET "http://localhost:8000/api/v2/dashboards/student/" \
  -H "Authorization: Bearer <token-estudiante>"
```

### Reporte Prácticas (Excel)

```bash
curl -X GET "http://localhost:8000/api/v2/reports/practices/?status=IN_PROGRESS&format=excel" \
  -H "Authorization: Bearer <token>" \
  --output reporte_practicas.xlsx
```

### Estadísticas con Filtros

```bash
curl -X GET "http://localhost:8000/api/v2/dashboards/statistics/?period=quarter&start_date=2024-07-01&end_date=2024-09-30" \
  -H "Authorization: Bearer <token>"
```

### Certificado de Práctica

```bash
curl -X GET "http://localhost:8000/api/v2/reports/25/certificate/" \
  -H "Authorization: Bearer <token>"
```

---

## 🎨 Integración con Frontend

### React con Chart.js

```javascript
// Obtener datos para gráfica
const response = await fetch('/api/v2/dashboards/charts/?type=practices_status', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const { data } = await response.json();

// Usar directamente con Chart.js
<Pie data={data} />
```

### Vue con Recharts

```vue
<template>
  <PieChart :data="chartData" />
</template>

<script>
export default {
  async mounted() {
    const res = await this.$axios.get('/api/v2/dashboards/charts/', {
      params: { type: 'students_career' }
    });
    this.chartData = res.data.data;
  }
}
</script>
```

### Angular con Dashboard

```typescript
export class DashboardComponent implements OnInit {
  dashboardData: any;

  ngOnInit() {
    this.dashboardService.getGeneral().subscribe(data => {
      this.dashboardData = data.data;
      this.renderCharts();
    });
  }
}
```

---

## 📥 Exportación de Datos

### Formatos Soportados

1. **JSON**: Respuesta estándar de la API
2. **Excel (.xlsx)**: 
   - Formato profesional
   - Headers con estilo
   - Columnas auto-ajustadas
   - Requiere: `pip install openpyxl`
3. **CSV (.csv)**:
   - Compatible con Excel
   - Separador: coma
   - Encoding: UTF-8

### Ejemplo Exportación Excel

```bash
# Exportar prácticas a Excel
curl -X GET "http://localhost:8000/api/v2/reports/practices/?format=excel&status=COMPLETED" \
  -H "Authorization: Bearer <token>" \
  --output practicas_completadas.xlsx

# Exportar estudiantes a CSV
curl -X GET "http://localhost:8000/api/v2/reports/students/?format=csv&career=Ingeniería" \
  -H "Authorization: Bearer <token>" \
  --output estudiantes_ingenieria.csv
```

---

## 🔄 Caching y Performance

### Recomendaciones

1. **Cache dashboards** (Redis):
```python
cache_key = f'dashboard_general_{user_id}'
cached_data = cache.get(cache_key)
if not cached_data:
    cached_data = generate_dashboard()
    cache.set(cache_key, cached_data, timeout=300)  # 5 minutos
```

2. **Paginar reportes grandes**:
```http
GET /api/v2/reports/practices/?page=1&page_size=100
```

3. **Procesar exportaciones asíncronas** (Celery):
```python
from celery import shared_task

@shared_task
def generate_excel_report(filters):
    # Generar reporte
    # Enviar por email o guardar en storage
```

---

## 🚀 Próximos Pasos

- [ ] Implementar generación de PDF para certificados
- [ ] Agregar más tipos de gráficas
- [ ] Implementar caching con Redis
- [ ] Exportación asíncrona para reportes grandes
- [ ] Dashboard en tiempo real con WebSockets
- [ ] Notificaciones push para métricas críticas

---

**Autor**: Sistema de Gestión de Prácticas Profesionales - UPEU  
**Fase 7**: Dashboard Endpoints  
**Fecha**: Octubre 2024
