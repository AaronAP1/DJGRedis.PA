# 📊 Análisis: Base de Datos PostgreSQL vs Models Django

## ✅ **RESUMEN EJECUTIVO**

**Estado General**: Tus models Django tienen **PARCIALMENTE** mapeados los modelos importantes del negocio.

**Modelos Core Mapeados**: 6/10 (60%)
**Modelos Faltantes Críticos**: 4

---

## 🎯 **TABLAS DE NEGOCIO EN LA BD vs MODELS DJANGO**

### ✅ **MODELOS YA IMPLEMENTADOS (Correctamente mapeados)**

| Tabla BD | Model Django | Estado | Uso en APIs |
|----------|--------------|--------|-------------|
| `users` | `User` | ✅ Completo | REST + GraphQL |
| `students` | `Student` | ✅ Completo | REST + GraphQL |
| `companies` | `Company` | ✅ Completo | REST + GraphQL |
| `supervisors` | `Supervisor` | ✅ Completo | REST + GraphQL |
| `practices` | `Practice` | ✅ Completo | REST + GraphQL |
| `documents` | `Document` | ✅ Completo | REST + GraphQL |
| `notifications` | `Notification` | ✅ Completo | REST + GraphQL |
| `roles` | `Role` | ✅ Completo | REST + GraphQL |
| `permissions` | `Permission` | ✅ Completo | REST + GraphQL |

---

### ❌ **TABLAS IMPORTANTES FALTANTES EN MODELS**

#### 1. **`upeu_evaluacion_practica`** (CRÍTICO ⚠️)
**Estado**: ❌ NO MAPEADO
**Importancia**: **ALTA** - Evaluaciones de supervisores
**Estructura BD**:
```sql
CREATE TABLE public.upeu_evaluacion_practica (
    id integer NOT NULL,
    practica_id integer,                    -- FK a práctica
    evaluador_id integer,                   -- FK a usuario evaluador
    tipo_evaluador varchar(20),             -- 'SUPERVISOR', 'COORDINADOR'
    criterios_evaluacion jsonb,             -- JSON con criterios
    puntaje_total numeric(5,2),             -- 0-100
    comentarios text,
    recomendaciones text,
    fecha_evaluacion timestamp,
    periodo_evaluacion varchar(50)          -- 'MENSUAL', 'FINAL', etc.
)
```

**Uso en APIs**: 
- ✅ Necesario para GraphQL mutation `createEvaluation`
- ✅ Query `evaluationsByPractice`
- ✅ Reporte de evaluaciones

**Solución**: Crear modelo `PracticeEvaluation`

---

#### 2. **`upeu_escuela`** (IMPORTANTE 📚)
**Estado**: ❌ NO MAPEADO
**Importancia**: **MEDIA** - Gestión académica
**Estructura BD**:
```sql
CREATE TABLE public.upeu_escuela (
    id integer NOT NULL,
    nombre varchar(150) NOT NULL,           -- 'Ingeniería de Sistemas'
    codigo varchar(10) UNIQUE,              -- 'EP-IS'
    facultad varchar(150),                  -- 'Ingeniería'
    coordinador_id integer,                 -- FK a usuario coordinador
    activa boolean DEFAULT true,
    fecha_creacion timestamp
)
```

**Uso en APIs**:
- Query `schools` (lista de escuelas)
- Filtrar estudiantes por escuela
- Asignar coordinador a escuela

**Solución**: Crear modelo `School`

---

#### 3. **`upeu_rama`** (IMPORTANTE 🌿)
**Estado**: ❌ NO MAPEADO  
**Importancia**: **MEDIA** - Especialización de carreras
**Estructura BD**:
```sql
CREATE TABLE public.upeu_rama (
    id integer NOT NULL,
    nombre varchar(100) NOT NULL,           -- 'Desarrollo de Software'
    descripcion text,
    escuela_id integer,                     -- FK a escuela
    activa boolean DEFAULT true,
    fecha_creacion timestamp
)
```

**Uso en APIs**:
- Filtrar prácticas por especialidad
- Matching empresa-estudiante por rama

**Solución**: Crear modelo `Branch` o `Specialization`

---

#### 4. **`upeu_historial_estado_practica`** (AUDITORÍA 📜)
**Estado**: ❌ NO MAPEADO
**Importancia**: **MEDIA-ALTA** - Trazabilidad
**Estructura BD**:
```sql
CREATE TABLE public.upeu_historial_estado_practica (
    id integer NOT NULL,
    practica_id integer,
    estado_anterior varchar(50),
    estado_nuevo varchar(50),
    usuario_responsable_id integer,
    motivo text,
    fecha_cambio timestamp DEFAULT CURRENT_TIMESTAMP
)
```

**Uso en APIs**:
- Timeline de estados de práctica
- Auditoría de cambios
- Reportes de flujo de trabajo

**Solución**: Crear modelo `PracticeStatusHistory`

---

#### 5. **`upeu_documento_practica`** (DOCUMENTOS ESPECÍFICOS 📄)
**Estado**: ⚠️ PARCIALMENTE (tienes `Document` genérico)
**Importancia**: **MEDIA**
**Estructura BD**:
```sql
CREATE TABLE public.upeu_documento_practica (
    id integer NOT NULL,
    practica_id integer,
    tipo_documento_id integer,              -- FK a tipo de documento
    titulo varchar(200),
    descripcion text,
    archivo_url varchar(500),
    estado public.estado_documento,         -- PENDIENTE, VALIDADO, RECHAZADO
    version integer DEFAULT 1,
    documento_anterior_id integer,          -- Versionado
    subido_por integer,
    validado_por integer,
    fecha_subida timestamp,
    fecha_validacion timestamp,
    observaciones text
)
```

**Diferencia con tu modelo**:
- ✅ Tu modelo `Document` es más simple
- ❌ No tiene versionado
- ❌ No tiene estados PENDIENTE/VALIDADO/RECHAZADO
- ❌ No tiene FK a `tipo_documento`

**Solución**: Extender modelo `Document` actual

---

#### 6. **`upeu_reporte_practica`** (REPORTES 📊)
**Estado**: ❌ NO MAPEADO
**Importancia**: **BAJA-MEDIA** (puede generarse en tiempo real)
**Estructura BD**:
```sql
CREATE TABLE public.upeu_reporte_practica (
    id integer NOT NULL,
    practica_id integer,
    periodo varchar(50),                    -- 'SEMANAL', 'MENSUAL'
    tipo_reporte varchar(50),               -- 'AVANCE', 'FINAL'
    contenido jsonb,                        -- JSON con detalles
    generado_por integer,
    fecha_generacion timestamp,
    fecha_inicio_periodo date,
    fecha_fin_periodo date
)
```

**Uso en APIs**:
- Dashboard de reportes
- Exportación a PDF
- Seguimiento periódico

**Solución**: OPCIONAL - Puede generarse dinámicamente

---

### ⚠️ **TABLAS DE CONFIGURACIÓN/ADMINISTRACIÓN**

Estas NO necesitan estar en tus models si no se usan en APIs de negocio:

| Tabla BD | ¿Necesario? | Motivo |
|----------|-------------|--------|
| `upeu_configuracion` | ❌ NO | Configuración del sistema (no API) |
| `upeu_coordinador_escuela` | ⚠️ OPCIONAL | Relación coordinador-escuela (puede ir en `School`) |
| `upeu_perfil_admin` | ❌ NO | Ya tienes `User` con roles |
| `upeu_perfil_secretaria` | ❌ NO | Ya tienes `User` con roles |
| `upeu_perfil_superadmin` | ❌ NO | Ya tienes `User` con roles |
| `upeu_perfil_supervisor` | ✅ SÍ | Ya mapeado como `Supervisor` |
| `upeu_perfil_practicante` | ✅ SÍ | Ya mapeado como `Student` |
| `upeu_log_auditoria` | ❌ NO | Logs de auditoría (Django Axes ya lo hace) |
| `upeu_sesion_usuario` | ❌ NO | Django maneja sesiones |
| `upeu_tipo_documento` | ⚠️ OPCIONAL | Tipos de documentos (puede ser ENUM) |
| `upeu_oportunidad_laboral` | ❌ NO | Feature adicional (no core) |
| `upeu_postulacion_oportunidad` | ❌ NO | Feature adicional (no core) |
| `upeu_mensaje` | ⚠️ OPCIONAL | Sistema de mensajería (feature adicional) |
| `upeu_notificacion` | ✅ SÍ | Ya mapeado como `Notification` |
| `upeu_rol` | ✅ SÍ | Ya mapeado como `Role` |
| `upeu_usuario` | ✅ SÍ | Ya mapeado como `User` |
| `upeu_validacion` | ❌ NO | Validaciones genéricas (lógica de negocio) |

---

## 🚨 **MODELOS CRÍTICOS QUE DEBES IMPLEMENTAR**

### Prioridad 1 - URGENTE ⚠️

#### `PracticeEvaluation` (Evaluaciones)
```python
class PracticeEvaluation(models.Model):
    """Evaluación de práctica por supervisor o coordinador."""
    
    TIPO_EVALUADOR_CHOICES = [
        ('SUPERVISOR', 'Supervisor de empresa'),
        ('COORDINADOR', 'Coordinador académico'),
    ]
    
    PERIODO_CHOICES = [
        ('INICIAL', 'Evaluación inicial'),
        ('MENSUAL_1', 'Evaluación mensual 1'),
        ('MENSUAL_2', 'Evaluación mensual 2'),
        ('MENSUAL_3', 'Evaluación mensual 3'),
        ('FINAL', 'Evaluación final'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4)
    practice = models.ForeignKey(Practice, on_delete=models.CASCADE, related_name='evaluations')
    evaluator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='evaluations_made')
    tipo_evaluador = models.CharField(max_length=20, choices=TIPO_EVALUADOR_CHOICES)
    periodo_evaluacion = models.CharField(max_length=50, choices=PERIODO_CHOICES)
    
    # Criterios de evaluación
    criterios_evaluacion = models.JSONField(default=dict, help_text='JSON con criterios específicos')
    puntaje_total = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    comentarios = models.TextField(blank=True)
    recomendaciones = models.TextField(blank=True)
    
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'practice_evaluations'
        verbose_name = 'Evaluación de Práctica'
        verbose_name_plural = 'Evaluaciones de Prácticas'
        unique_together = [['practice', 'periodo_evaluacion']]
```

---

### Prioridad 2 - IMPORTANTE 📚

#### `School` (Escuelas/Carreras)
```python
class School(models.Model):
    """Escuela Profesional / Carrera."""
    
    id = models.UUIDField(primary_key=True, default=uuid4)
    nombre = models.CharField('Nombre', max_length=150)
    codigo = models.CharField('Código', max_length=10, unique=True)
    facultad = models.CharField('Facultad', max_length=150)
    coordinador = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='coordinated_schools'
    )
    activa = models.BooleanField('Activa', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'schools'
        verbose_name = 'Escuela Profesional'
        verbose_name_plural = 'Escuelas Profesionales'
```

#### `Branch` (Ramas/Especialidades)
```python
class Branch(models.Model):
    """Rama o especialidad dentro de una escuela."""
    
    id = models.UUIDField(primary_key=True, default=uuid4)
    nombre = models.CharField('Nombre', max_length=100)
    descripcion = models.TextField('Descripción', blank=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='branches')
    activa = models.BooleanField('Activa', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'branches'
        verbose_name = 'Rama/Especialidad'
        verbose_name_plural = 'Ramas/Especialidades'
```

---

### Prioridad 3 - DESEABLE 📜

#### `PracticeStatusHistory` (Historial de estados)
```python
class PracticeStatusHistory(models.Model):
    """Historial de cambios de estado de prácticas."""
    
    id = models.UUIDField(primary_key=True, default=uuid4)
    practice = models.ForeignKey(Practice, on_delete=models.CASCADE, related_name='status_history')
    estado_anterior = models.CharField(max_length=50)
    estado_nuevo = models.CharField(max_length=50)
    usuario_responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    motivo = models.TextField(blank=True)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'practice_status_history'
        verbose_name = 'Historial de Estado'
        verbose_name_plural = 'Historiales de Estados'
        ordering = ['-fecha_cambio']
```

---

## 📋 **MODIFICACIONES RECOMENDADAS A MODELOS EXISTENTES**

### 1. **Student** - Agregar relaciones
```python
# AÑADIR:
school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, related_name='students')
branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
```

### 2. **Document** - Agregar estados y versionado
```python
# AÑADIR:
STATUS_CHOICES = [
    ('PENDING', 'Pendiente'),
    ('VALIDATED', 'Validado'),
    ('REJECTED', 'Rechazado'),
    ('OBSERVED', 'Observado'),
]
status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
version = models.PositiveIntegerField(default=1)
previous_version = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_documents')
validation_date = models.DateTimeField(null=True, blank=True)
observations = models.TextField(blank=True)
```

### 3. **Practice** - Agregar campos faltantes
```python
# AÑADIR:
horas_requeridas = models.PositiveIntegerField('Horas requeridas', default=480)
horas_completadas = models.PositiveIntegerField('Horas completadas', default=0)
remunerada = models.BooleanField('Remunerada', default=False)
monto_remuneracion = models.DecimalField(max_digits=10, decimal_places=2, default=0)
coordinador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='coordinated_practices')
secretaria = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assisted_practices')
```

---

## 📊 **RESUMEN DE ACCIONES**

### ✅ **Implementar AHORA** (Crítico para APIs)
1. ✅ **PracticeEvaluation** - Evaluaciones de supervisores
2. ✅ **School** - Escuelas profesionales
3. ✅ **Branch** - Especialidades/ramas

### ⚠️ **Implementar PRONTO** (Importante)
4. Modificar **Student** - Agregar FK a School y Branch
5. Modificar **Document** - Agregar estados y versionado
6. Modificar **Practice** - Agregar campos de horas, remuneración, coordinador

### 📅 **Implementar DESPUÉS** (Opcional/Deseable)
7. **PracticeStatusHistory** - Historial de estados
8. **DocumentType** - Tipos de documentos (si necesitas clasificación avanzada)
9. **Report** - Reportes (solo si necesitas persistirlos)

---

## 🎯 **CONCLUSIÓN**

**Estado Actual**: 
- ✅ Tienes el **60% de modelos core** implementados
- ⚠️ Falta el **modelo crítico PracticeEvaluation** (usado en APIs)
- ⚠️ Faltan relaciones académicas (School, Branch)

**Impacto en APIs**:
- REST API: **FUNCIONAL** pero limitado (no evaluaciones, no escuelas)
- GraphQL API: **FUNCIONAL** pero incompleto (queries de evaluaciones fallarán)

**Recomendación**:
1. Crear **PracticeEvaluation** inmediatamente
2. Crear **School** y **Branch** en próxima iteración
3. Modificar modelos existentes según necesidad

**Prioridad de implementación**: 🔴 ALTA para PracticeEvaluation
