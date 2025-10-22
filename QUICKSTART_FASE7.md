# 🚀 Inicio Rápido - Fase 7 Dashboard Endpoints

## ⚡ Configuración Rápida

### 1. Habilitar REST API v2

En `config/urls.py`, descomenta la línea:

```python
# ========================================================================
# REST API v2 (ViewSets completos - Fase 3 + Dashboards Fase 7)
# ========================================================================
path('api/v2/', include('src.adapters.primary.rest_api.urls_api_v2')),  # ← Descomentar esta línea
```

### 2. Instalar dependencia opcional para Excel

```bash
pip install openpyxl
```

### 3. Iniciar servidor

```bash
python manage.py runserver
```

---

## 🧪 Probar Endpoints

### Dashboard General (Coordinador/Admin)

```bash
# 1. Login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "coordinador@upeu.edu.pe",
    "password": "tu_password"
  }'

# 2. Dashboard
curl -X GET http://localhost:8000/api/v2/dashboards/general/ \
  -H "Authorization: Bearer <tu_token>"
```

### Dashboard Estudiante

```bash
# Login como estudiante
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "estudiante@upeu.edu.pe",
    "password": "tu_password"
  }'

# Dashboard
curl -X GET http://localhost:8000/api/v2/dashboards/student/ \
  -H "Authorization: Bearer <tu_token>"
```

### Datos para Gráficas

```bash
curl -X GET "http://localhost:8000/api/v2/dashboards/charts/?type=practices_status" \
  -H "Authorization: Bearer <tu_token>"
```

### Reporte de Prácticas (JSON)

```bash
curl -X GET "http://localhost:8000/api/v2/reports/practices/?status=IN_PROGRESS" \
  -H "Authorization: Bearer <tu_token>"
```

### Reporte de Prácticas (Excel)

```bash
curl -X GET "http://localhost:8000/api/v2/reports/practices/?format=excel&status=COMPLETED" \
  -H "Authorization: Bearer <tu_token>" \
  --output reporte_practicas.xlsx
```

### Estadísticas con Filtros

```bash
curl -X GET "http://localhost:8000/api/v2/dashboards/statistics/?period=month&start_date=2024-09-01&end_date=2024-10-17" \
  -H "Authorization: Bearer <tu_token>"
```

---

## 🌐 Probar en Navegador

### Swagger UI
```
http://localhost:8000/api/docs/
```

1. Click en "Authorize"
2. Ingresa token: `Bearer <tu_token>`
3. Navega a sección "dashboards" o "reports"
4. Prueba los endpoints

### GraphiQL
```
http://localhost:8000/graphql/
```

Query de ejemplo:
```graphql
query {
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
  }
}
```

---

## 📊 Endpoints Disponibles

### Dashboards

| Endpoint | Método | Requiere | Descripción |
|----------|--------|----------|-------------|
| `/api/v2/dashboards/general/` | GET | Coordinador/Admin | Dashboard completo |
| `/api/v2/dashboards/student/` | GET | Estudiante | Dashboard estudiante |
| `/api/v2/dashboards/supervisor/` | GET | Supervisor | Dashboard supervisor |
| `/api/v2/dashboards/secretary/` | GET | Secretaría | Dashboard secretaría |
| `/api/v2/dashboards/statistics/` | GET | Coordinador/Admin | Estadísticas completas |
| `/api/v2/dashboards/charts/` | GET | Autenticado | Datos para gráficas |

### Reportes

| Endpoint | Método | Requiere | Descripción |
|----------|--------|----------|-------------|
| `/api/v2/reports/practices/` | GET | Coord/Admin/Secret | Reporte prácticas |
| `/api/v2/reports/students/` | GET | Coord/Admin/Secret | Reporte estudiantes |
| `/api/v2/reports/companies/` | GET | Coord/Admin/Secret | Reporte empresas |
| `/api/v2/reports/statistics_summary/` | GET | Coordinador/Admin | Resumen estadístico |
| `/api/v2/reports/{id}/certificate/` | GET | Usuario relacionado | Certificado práctica |

---

## 🎨 Ejemplo de Integración Frontend

### React

```javascript
// Dashboard Component
import { useState, useEffect } from 'react';
import { Pie } from 'react-chartjs-2';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [chartData, setChartData] = useState(null);

  useEffect(() => {
    // Obtener estadísticas
    fetch('/api/v2/dashboards/general/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    .then(res => res.json())
    .then(data => setStats(data.data));

    // Obtener datos de gráfica
    fetch('/api/v2/dashboards/charts/?type=practices_status', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    .then(res => res.json())
    .then(data => setChartData(data.data));
  }, []);

  if (!stats) return <div>Cargando...</div>;

  return (
    <div>
      <h1>Dashboard General</h1>
      
      <div className="stats">
        <div className="stat-card">
          <h3>Prácticas Totales</h3>
          <p>{stats.practices.total}</p>
        </div>
        <div className="stat-card">
          <h3>En Progreso</h3>
          <p>{stats.practices.in_progress}</p>
        </div>
        <div className="stat-card">
          <h3>Completadas</h3>
          <p>{stats.practices.completed}</p>
        </div>
      </div>

      {chartData && (
        <div className="chart">
          <h2>Estado de Prácticas</h2>
          <Pie data={chartData} />
        </div>
      )}
    </div>
  );
}

export default Dashboard;
```

### Vue

```vue
<template>
  <div class="dashboard">
    <h1>Dashboard General</h1>
    
    <v-row>
      <v-col cols="12" md="4" v-for="stat in statsCards" :key="stat.title">
        <v-card>
          <v-card-title>{{ stat.title }}</v-card-title>
          <v-card-text>
            <div class="text-h3">{{ stat.value }}</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>Estado de Prácticas</v-card-title>
          <v-card-text>
            <pie-chart :data="practicesChart" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script>
export default {
  data() {
    return {
      stats: null,
      practicesChart: null
    }
  },
  computed: {
    statsCards() {
      if (!this.stats) return [];
      return [
        {
          title: 'Prácticas Totales',
          value: this.stats.practices.total
        },
        {
          title: 'En Progreso',
          value: this.stats.practices.in_progress
        },
        {
          title: 'Completadas',
          value: this.stats.practices.completed
        }
      ];
    }
  },
  async mounted() {
    // Cargar estadísticas
    const statsRes = await this.$axios.get('/api/v2/dashboards/general/');
    this.stats = statsRes.data.data;

    // Cargar gráfica
    const chartRes = await this.$axios.get('/api/v2/dashboards/charts/', {
      params: { type: 'practices_status' }
    });
    this.practicesChart = chartRes.data.data;
  }
}
</script>
```

---

## 📥 Exportar Reportes

### Desde Terminal

```bash
# Excel
curl -X GET "http://localhost:8000/api/v2/reports/practices/?format=excel&status=COMPLETED" \
  -H "Authorization: Bearer <token>" \
  --output practicas_completadas.xlsx

# CSV
curl -X GET "http://localhost:8000/api/v2/reports/students/?format=csv" \
  -H "Authorization: Bearer <token>" \
  --output estudiantes.csv
```

### Desde JavaScript

```javascript
async function exportReport(type, format) {
  const response = await fetch(
    `/api/v2/reports/${type}/?format=${format}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `reporte_${type}_${new Date().toISOString()}.${format}`;
  a.click();
}

// Uso
exportReport('practices', 'excel');
exportReport('students', 'csv');
```

---

## 🐛 Troubleshooting

### Error: "openpyxl not found"

```bash
pip install openpyxl
```

### Error: 401 Unauthorized

Verifica que el token sea válido:

```bash
# Obtener nuevo token
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "tu@email.com", "password": "tu_password"}'
```

### Error: 403 Forbidden

Verifica que tu usuario tenga el rol correcto:
- Dashboard general: Coordinador o Administrador
- Reportes: Coordinador, Administrador o Secretaría
- Dashboard estudiante: Practicante

### Error: Module not found

Asegúrate de que todos los imports estén correctos:

```bash
# Verificar estructura
python scripts/verify_fase7.py
```

---

## 📚 Documentación Completa

- **Fase 7 Resumen**: `src/adapters/primary/FASE7_RESUMEN.md`
- **Dashboards README**: `src/adapters/primary/rest_api/views/README_DASHBOARDS.md`
- **Proyecto Completo**: `PROYECTO_RESUMEN_COMPLETO.md`
- **Swagger UI**: http://localhost:8000/api/docs/
- **GraphQL Docs**: http://localhost:8000/graphql/

---

## ✅ Checklist de Verificación

- [ ] REST API v2 habilitada en `config/urls.py`
- [ ] `openpyxl` instalado (para Excel)
- [ ] Servidor iniciado y funcionando
- [ ] Token de autenticación obtenido
- [ ] Dashboard general accesible
- [ ] Reportes funcionando
- [ ] Exportación Excel/CSV funciona
- [ ] Gráficas retornan datos correctos

---

## 🎉 ¡Listo!

Ya puedes usar todos los endpoints de Dashboard y Reportes.

**Siguiente paso**: Completar Fase 8 (Documentación Final)

---

**¿Necesitas ayuda?** Consulta la documentación completa en los archivos README mencionados arriba.
