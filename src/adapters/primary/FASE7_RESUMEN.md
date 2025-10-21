# 🎉 Fase 7 Completada - Dashboard Endpoints

## ✅ Resumen de Implementación

### 📦 Archivos Creados:

1. **`views/dashboards.py`** (~950 líneas)
   - DashboardViewSet con 6 endpoints principales
   - Dashboards personalizados por rol
   - Estadísticas en tiempo real
   - Datos para gráficas (Chart.js compatible)

2. **`views/reports.py`** (~850 líneas)
   - ReportsViewSet con 5 endpoints
   - Reportes con filtros avanzados
   - Exportación Excel/CSV
   - Certificados de prácticas
   - Resúmenes estadísticos

3. **`views/__init__.py`**
   - Exportación de ViewSets
   - Organización modular

4. **`views/README_DASHBOARDS.md`** (~650 líneas)
   - Documentación completa
   - Ejemplos de uso
   - Guías de integración

5. **`urls_api_v2.py`** (actualizado)
   - Registro de nuevos ViewSets
   - Rutas dashboard y reports

---

## 🎯 Endpoints Implementados

### Dashboard Endpoints (6)

| Endpoint | Método | Descripción | Requiere |
|----------|--------|-------------|----------|
| `/dashboards/general/` | GET | Dashboard completo del sistema | Coordinador/Admin |
| `/dashboards/student/` | GET | Dashboard estudiante con progreso | Practicante |
| `/dashboards/supervisor/` | GET | Dashboard supervisor con asignaciones | Supervisor |
| `/dashboards/secretary/` | GET | Dashboard secretaría con validaciones | Secretaría |
| `/dashboards/statistics/` | GET | Estadísticas completas con filtros | Coordinador/Admin |
| `/dashboards/charts/` | GET | Datos formateados para gráficas | Autenticado |

### Report Endpoints (5)

| Endpoint | Método | Descripción | Requiere |
|----------|--------|-------------|----------|
| `/reports/practices/` | GET | Reporte de prácticas con filtros | Coord/Admin/Secret |
| `/reports/students/` | GET | Reporte de estudiantes | Coord/Admin/Secret |
| `/reports/companies/` | GET | Reporte de empresas | Coord/Admin/Secret |
| `/reports/statistics_summary/` | GET | Resumen estadístico completo | Coordinador/Admin |
| `/reports/{id}/certificate/` | GET | Certificado de práctica | Usuario relacionado |

**Total**: 11 nuevos endpoints especializados

---

## 📊 Características Principales

### 1. Dashboards por Rol

#### 🎓 Dashboard Coordinador/Administrador
```json
{
  "practices": {
    "total": 150,
    "by_status": {...},
    "pending_approval": 12
  },
  "students": {
    "total": 500,
    "eligible": 350,
    "with_practice": 150
  },
  "companies": {
    "total": 75,
    "validated": 68,
    "by_sector": [...]
  },
  "recent_activities": [...]
}
```

**Métricas incluidas**:
- Prácticas: Total, por estado, pendientes
- Estudiantes: Total, elegibles, con/sin práctica
- Empresas: Total, validadas, por sector
- Documentos: Total, por estado
- Actividades recientes: Últimas 10

---

#### 👨‍🎓 Dashboard Estudiante
```json
{
  "profile": {
    "codigo": "2024012345",
    "carrera": "Ingeniería de Sistemas",
    "promedio": 15.5,
    "elegible_practicas": true
  },
  "current_practice": {
    "titulo": "Desarrollo Web",
    "estado": "IN_PROGRESS",
    "horas_completadas": 320,
    "horas_totales": 640
  },
  "practice_progress": {
    "porcentaje_completado": 50.0,
    "horas_restantes": 320
  },
  "hours_summary": {
    "by_month": [...],
    "promedio_semanal": 20.0
  }
}
```

**Métricas incluidas**:
- Perfil académico completo
- Práctica actual con detalles
- Progreso con porcentajes
- Resumen de horas por mes
- Promedio semanal de horas
- Documentos pendientes
- Notificaciones no leídas

---

#### 👔 Dashboard Supervisor
```json
{
  "profile": {
    "nombre": "María González",
    "cargo": "Jefe de Desarrollo",
    "company": {...}
  },
  "practices_statistics": {
    "total": 15,
    "by_status": {...}
  },
  "active_practices": [
    {
      "student": {...},
      "progreso": 50.0
    }
  ],
  "students_performance": [...]
}
```

**Métricas incluidas**:
- Información del supervisor y empresa
- Estadísticas de prácticas asignadas
- Lista de prácticas activas con progreso
- Evaluaciones pendientes
- Rendimiento de estudiantes supervisados

---

#### 📋 Dashboard Secretaría
```json
{
  "pending_validations": {
    "companies": 8,
    "documents": 15,
    "practices": 10,
    "total": 33
  },
  "recent_registrations": {
    "students": 25,
    "companies": 3,
    "practices": 12
  },
  "companies_to_validate": [...]
}
```

**Métricas incluidas**:
- Validaciones pendientes (empresas, docs, prácticas)
- Registros recientes (últimos 7 días)
- Estado de documentos
- Lista detallada de empresas por validar

---

### 2. Estadísticas Avanzadas

#### Estadísticas con Filtros de Período
```http
GET /api/v2/dashboards/statistics/
    ?period=month|quarter|year
    &start_date=2024-01-01
    &end_date=2024-12-31
```

**Datos incluidos**:
- Línea temporal de prácticas
- Distribución estudiantes por carrera
- Distribución empresas por sector
- Tasa de completación
- Promedio de horas
- Satisfacción promedio

---

### 3. Datos para Gráficas

#### Formatos Chart.js Compatible
```http
GET /api/v2/dashboards/charts/?type=practices_status
```

**Response**:
```json
{
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

**Tipos de gráficas**:
1. `practices_status`: Estado de prácticas (pie/donut)
2. `students_career`: Estudiantes por carrera (bar)
3. `companies_sector`: Empresas por sector (bar)
4. `practices_timeline`: Línea temporal (line)

---

### 4. Reportes con Filtros

#### Reporte de Prácticas
```http
GET /api/v2/reports/practices/
    ?status=IN_PROGRESS,COMPLETED
    &start_date=2024-01-01
    &end_date=2024-12-31
    &career=Ingeniería de Sistemas
    &company_id=10
    &format=json|excel|csv
```

**Filtros disponibles**:
- Estado(s) de práctica
- Rango de fechas
- Carrera profesional
- Empresa específica
- Formato de salida

**Datos exportados**:
- Información completa del estudiante
- Datos de la empresa y supervisor
- Fechas y horas (totales, completadas, %)
- Estado y modalidad

---

#### Reporte de Estudiantes
```http
GET /api/v2/reports/students/
    ?career=Ingeniería de Sistemas
    &semester=6,7,8
    &with_practice=true|false
    &format=json|excel|csv
```

**Filtros**:
- Carrera profesional
- Semestre(s) actual
- Con/sin práctica

**Datos**:
- Código, nombre, email
- Carrera, semestre, promedio
- Elegibilidad para prácticas
- Práctica actual (si tiene)
- Total de prácticas realizadas

---

#### Reporte de Empresas
```http
GET /api/v2/reports/companies/
    ?sector=Tecnología
    &validated=true|false
    &status=ACTIVE,SUSPENDED
    &format=json|excel|csv
```

**Filtros**:
- Sector económico
- Estado de validación
- Estado de empresa

**Datos**:
- RUC, razón social, contacto
- Sector, dirección
- Estado de validación
- Estadísticas: total prácticas, activas, completadas, supervisores

---

### 5. Exportación de Datos

#### Formatos Soportados

**1. JSON** (Default)
- Respuesta estándar de la API
- Estructura completa con metadatos

**2. Excel (.xlsx)**
- Formato profesional
- Headers con estilo (fondo azul, texto blanco, negrita)
- Columnas auto-ajustadas
- Requiere: `pip install openpyxl`

**3. CSV (.csv)**
- Compatible con Excel
- UTF-8 encoding
- Separador: coma

#### Ejemplo Exportación
```bash
# Excel
curl -X GET "http://localhost:8000/api/v2/reports/practices/?format=excel&status=COMPLETED" \
  -H "Authorization: Bearer <token>" \
  --output practicas.xlsx

# CSV
curl -X GET "http://localhost:8000/api/v2/reports/students/?format=csv" \
  -H "Authorization: Bearer <token>" \
  --output estudiantes.csv
```

---

### 6. Certificados de Práctica

```http
GET /api/v2/reports/{practice_id}/certificate/
```

**Requisitos**:
- Práctica debe estar en estado `COMPLETED`
- Usuario debe tener relación con la práctica:
  - Estudiante de la práctica
  - Supervisor asignado
  - Coordinador/Administrador

**Datos del certificado**:
- Información completa de la práctica
- Datos del estudiante (código, nombre, carrera)
- Datos de la empresa (RUC, razón social, sector)
- Datos del supervisor (nombre, cargo, email)
- Calificación final
- Observaciones
- Número de certificado único
- Fecha de generación

**Formato número de certificado**: `CERT-{id:06d}-{year}`  
Ejemplo: `CERT-000025-2024`

---

## 🔐 Matriz de Permisos

| Endpoint | ADMIN | COORD | SECRET | SUPER | ESTUD |
|----------|:-----:|:-----:|:------:|:-----:|:-----:|
| **Dashboards** |
| `general/` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `student/` | ❌ | ❌ | ❌ | ❌ | ✅ |
| `supervisor/` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `secretary/` | ❌ | ❌ | ✅ | ❌ | ❌ |
| `statistics/` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `charts/` | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Reports** |
| `practices/` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `students/` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `companies/` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `statistics_summary/` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `{id}/certificate/` | ✅ | ✅ | ❌ | ✅* | ✅* |

*Solo para prácticas relacionadas

---

## 📈 Métricas de Implementación

### Código
- **Líneas de código**: ~1,800 líneas
- **ViewSets**: 2 (DashboardViewSet, ReportsViewSet)
- **Endpoints**: 11 nuevos
- **Métodos auxiliares**: 15+
- **Tipos de gráficas**: 4

### Documentación
- **Líneas de documentación**: ~650 líneas
- **Ejemplos de uso**: 20+
- **Casos de uso cubiertos**: Todos los roles

### Funcionalidades
- **Dashboards por rol**: 4 (Coordinador, Estudiante, Supervisor, Secretaría)
- **Tipos de reportes**: 3 (Prácticas, Estudiantes, Empresas)
- **Formatos exportación**: 3 (JSON, Excel, CSV)
- **Filtros disponibles**: 15+
- **Estadísticas**: 30+ métricas diferentes

---

## 🎨 Integración con Frontend

### React + Chart.js
```javascript
// Dashboard Component
const Dashboard = () => {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    fetch('/api/v2/dashboards/general/', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => setData(data.data));
  }, []);
  
  return (
    <div>
      <h1>Dashboard General</h1>
      <PracticesChart data={data?.practices} />
      <StudentsStats data={data?.students} />
    </div>
  );
};

// Chart Component
const PracticesChart = () => {
  const [chartData, setChartData] = useState(null);
  
  useEffect(() => {
    fetch('/api/v2/dashboards/charts/?type=practices_status', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(res => setChartData(res.data));
  }, []);
  
  return <Pie data={chartData} />;
};
```

---

### Vue + Vuetify
```vue
<template>
  <v-container>
    <v-row>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>Prácticas</v-card-title>
          <v-card-text>
            <pie-chart :data="practicesData" />
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>Estadísticas</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item>
                <v-list-item-content>
                  <v-list-item-title>Total Prácticas</v-list-item-title>
                  <v-list-item-subtitle>{{ stats.practices.total }}</v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {
  data() {
    return {
      stats: null,
      practicesData: null
    }
  },
  async mounted() {
    // Obtener estadísticas
    const statsRes = await this.$axios.get('/api/v2/dashboards/general/');
    this.stats = statsRes.data.data;
    
    // Obtener datos de gráfica
    const chartRes = await this.$axios.get('/api/v2/dashboards/charts/', {
      params: { type: 'practices_status' }
    });
    this.practicesData = chartRes.data.data;
  }
}
</script>
```

---

### Angular + Material
```typescript
// dashboard.component.ts
import { Component, OnInit } from '@angular/core';
import { DashboardService } from './dashboard.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html'
})
export class DashboardComponent implements OnInit {
  dashboardData: any;
  chartData: any;
  
  constructor(private dashboardService: DashboardService) {}
  
  ngOnInit() {
    // Cargar dashboard
    this.dashboardService.getGeneral().subscribe(response => {
      this.dashboardData = response.data;
    });
    
    // Cargar datos de gráfica
    this.dashboardService.getChartData('practices_status').subscribe(response => {
      this.chartData = response.data;
    });
  }
  
  exportReport(format: 'excel' | 'csv') {
    this.dashboardService.exportPracticesReport(format).subscribe(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `reporte.${format}`;
      a.click();
    });
  }
}

// dashboard.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private baseUrl = '/api/v2/dashboards';
  
  constructor(private http: HttpClient) {}
  
  getGeneral() {
    return this.http.get(`${this.baseUrl}/general/`);
  }
  
  getChartData(type: string) {
    return this.http.get(`${this.baseUrl}/charts/`, { params: { type } });
  }
  
  exportPracticesReport(format: string) {
    return this.http.get(`/api/v2/reports/practices/`, {
      params: { format },
      responseType: 'blob'
    });
  }
}
```

---

## 🚀 Casos de Uso

### 1. Coordinador revisa estado general
```
1. Login como coordinador
2. GET /api/v2/dashboards/general/
3. Visualiza métricas de todo el sistema
4. Identifica prácticas pendientes de aprobación
5. Toma decisiones basadas en datos
```

### 2. Estudiante monitorea su progreso
```
1. Login como estudiante
2. GET /api/v2/dashboards/student/
3. Ve su práctica actual y progreso
4. Revisa horas completadas y pendientes
5. Consulta documentos pendientes
```

### 3. Supervisor evalúa practicantes
```
1. Login como supervisor
2. GET /api/v2/dashboards/supervisor/
3. Ve lista de prácticas asignadas
4. Revisa rendimiento de cada estudiante
5. Identifica evaluaciones pendientes
```

### 4. Secretaría procesa validaciones
```
1. Login como secretaría
2. GET /api/v2/dashboards/secretary/
3. Ve empresas pendientes de validar
4. Revisa documentos pendientes
5. Procesa validaciones necesarias
```

### 5. Exportar reporte para análisis
```
1. Login como coordinador
2. GET /api/v2/reports/practices/?format=excel&status=COMPLETED
3. Descarga archivo Excel
4. Abre en Excel/LibreOffice
5. Realiza análisis adicional con tablas dinámicas
```

### 6. Generar certificado de práctica
```
1. Login como estudiante (práctica completada)
2. GET /api/v2/reports/25/certificate/
3. Recibe datos del certificado
4. Frontend genera PDF con datos
5. Descarga certificado oficial
```

---

## 📊 Queries y Optimizaciones

### Optimizaciones Implementadas

1. **select_related()**: Para ForeignKeys
```python
Practice.objects.select_related(
    'student__user',
    'company',
    'supervisor__user'
)
```

2. **prefetch_related()**: Para relaciones ManyToMany y reverse ForeignKey
```python
Student.objects.prefetch_related('practices')
```

3. **Anotaciones**: Para cálculos en base de datos
```python
Practice.objects.annotate(
    month=TruncMonth('fecha_registro')
).values('month').annotate(count=Count('id'))
```

4. **Agregaciones**: Para estadísticas
```python
Practice.objects.aggregate(
    avg_hours=Avg('horas_totales'),
    total=Count('id')
)
```

### Performance Tips

1. **Cachear dashboards frecuentes** (Redis):
```python
from django.core.cache import cache

cache_key = f'dashboard_student_{student.id}'
data = cache.get(cache_key)
if not data:
    data = generate_dashboard()
    cache.set(cache_key, data, timeout=300)  # 5 minutos
```

2. **Paginar reportes grandes**:
```python
from rest_framework.pagination import PageNumberPagination

paginator = PageNumberPagination()
paginator.page_size = 100
result_page = paginator.paginate_queryset(queryset, request)
```

3. **Exportación asíncrona** (Celery):
```python
@shared_task
def generate_large_report(filters):
    # Generar reporte en background
    # Enviar email con enlace de descarga
```

---

## 🏆 Progreso General

```
✅ Fase 1: Sistema de Permisos (40+ clases)
✅ Fase 2: Serializers (50+)
✅ Fase 3: ViewSets REST (65+ endpoints)
✅ Fase 4: GraphQL Mutations (30+)
✅ Fase 5: GraphQL Queries (50+)
✅ Fase 6: Configuración URLs (170+ endpoints)
✅ Fase 7: Dashboard Endpoints (11 endpoints) ← COMPLETADA
⏳ Fase 8: Documentación Final
```

**Progreso Total**: 87.5% (7/8 fases completadas)

---

## 📝 Endpoints Totales del Sistema

| Categoría | Cantidad | Descripción |
|-----------|----------|-------------|
| REST v1 (Legacy) | ~25 | Endpoints legacy |
| REST v2 (ViewSets) | 65 | CRUD completo (Fase 3) |
| REST v2 (Dashboards) | 6 | Dashboards por rol (Fase 7) |
| REST v2 (Reports) | 5 | Reportes y exportación (Fase 7) |
| GraphQL Queries | 50+ | Queries avanzadas (Fase 5) |
| GraphQL Mutations | 30+ | Mutations CRUD (Fase 4) |
| Documentación | 6 | Schema, Swagger, ReDoc |
| **TOTAL** | **~185** | Endpoints disponibles |

---

## 🚀 Siguiente: Fase 8 - Documentación Final

Documentación completa del sistema:
- Guía de instalación y deployment
- Arquitectura detallada
- Guías de usuario por rol
- Colección Postman actualizada
- Guía de desarrollo
- Testing y QA
- Troubleshooting

---

## 📚 Referencias

- **Django REST Framework**: https://www.django-rest-framework.org/
- **Chart.js**: https://www.chartjs.org/
- **openpyxl**: https://openpyxl.readthedocs.io/
- **Django Aggregation**: https://docs.djangoproject.com/en/5.0/topics/db/aggregation/

---

**Autor**: Sistema de Gestión de Prácticas Profesionales - UPEU  
**Fecha**: Octubre 2024  
**Fase 7**: ✅ **COMPLETADA EXITOSAMENTE**
