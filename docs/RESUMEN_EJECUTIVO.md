# 📊 RESUMEN EJECUTIVO - Sistema de Gestión de Prácticas Profesionales

## 🎯 Descripción General

Sistema web integral para administrar el ciclo completo de prácticas profesionales universitarias, desde el registro hasta la certificación, utilizando **Arquitectura Hexagonal (Ports and Adapters)** con Django.

### Objetivo
Automatizar y optimizar la gestión de prácticas pre-profesionales y profesionales de la Universidad Peruana Unión, garantizando trazabilidad completa, seguridad y cumplimiento de requisitos académicos.

---

## 👥 Roles del Sistema (5 Roles)

| Rol | Código | Descripción | Permisos | Alcance |
|-----|--------|-------------|----------|---------|
| **PRACTICANTE** | `PRACTICANTE` | Estudiante realizando prácticas | 5 permisos básicos | Solo recursos propios |
| **SUPERVISOR** | `SUPERVISOR` | Supervisor de empresa | 6 permisos evaluación | Prácticas asignadas |
| **SECRETARIA** | `SECRETARIA` | Personal administrativo | 15 permisos gestión | Validación y documentos |
| **COORDINADOR** | `COORDINADOR` | Coordinador académico | 32 permisos avanzados | Sistema completo |
| **ADMINISTRADOR** | `ADMINISTRADOR` | Admin del sistema | 40 permisos (completo) | Acceso total |

### Jerarquía de Roles

```
ADMINISTRADOR (Nivel 5)
    ↓
COORDINADOR (Nivel 4)
    ↓
SECRETARIA (Nivel 3)
    ↓
SUPERVISOR (Nivel 2)
    ↓
PRACTICANTE (Nivel 1)
```

---

## 🔄 Estados de Práctica (Máquina de Estados)

### Estados Disponibles (7 Estados)

```
┌─────────────┐
│   DRAFT     │ → Borrador (editable por estudiante)
└─────────────┘
       ↓
┌─────────────┐
│  PENDING    │ → Pendiente de aprobación
└─────────────┘
       ↓
┌─────────────┐
│  APPROVED   │ → Aprobada por coordinador
└─────────────┘
       ↓
┌─────────────┐
│ IN_PROGRESS │ → En ejecución
└─────────────┘
       ↓
┌─────────────┐
│  COMPLETED  │ → Finalizada con calificación ✅
└─────────────┘

Estados Alternativos:
├── CANCELLED   → Cancelada ❌
└── SUSPENDED   → Suspendida temporalmente ⏸️
```

### Transiciones Permitidas

```
DRAFT
  │
  ├─→ submit() [Estudiante] ─→ PENDING
  │
PENDING
  │
  ├─→ approve() [Coordinador] ─→ APPROVED
  ├─→ reject() [Coordinador] ─→ CANCELLED
  │
APPROVED
  │
  ├─→ start() [Estudiante/Coordinador] ─→ IN_PROGRESS
  ├─→ cancel() [Coordinador] ─→ CANCELLED
  │
IN_PROGRESS
  │
  ├─→ complete() [Coordinador] ─→ COMPLETED ✅
  ├─→ suspend() [Coordinador] ─→ SUSPENDED
  ├─→ cancel() [Coordinador] ─→ CANCELLED
  │
SUSPENDED
  │
  ├─→ resume() [Coordinador] ─→ IN_PROGRESS
  └─→ cancel() [Coordinador] ─→ CANCELLED
```

### Estados Finales

- **COMPLETED**: ✅ No permite cambios (éxito)
- **CANCELLED**: ❌ No permite cambios (terminado)

### Validaciones de Transición

| Estado Actual | Estados Permitidos | Quién puede cambiar |
|---------------|-------------------|---------------------|
| DRAFT | PENDING | PRACTICANTE |
| PENDING | APPROVED, CANCELLED | COORDINADOR |
| APPROVED | IN_PROGRESS, CANCELLED | ESTUDIANTE, COORDINADOR |
| IN_PROGRESS | COMPLETED, SUSPENDED, CANCELLED | COORDINADOR |
| SUSPENDED | IN_PROGRESS, CANCELLED | COORDINADOR |
| COMPLETED | (ninguno) | N/A |
| CANCELLED | (ninguno) | N/A |

---

## 🎭 Flujo Completo del Proceso

### Fase 1: Registro 📝 (PRACTICANTE)

**Duración**: 1-2 días

1. **Estudiante** crea solicitud de práctica (estado: `DRAFT`)
2. Ingresa información requerida:
   - 📍 Empresa (RUC, razón social, sector)
   - 👔 Supervisor (nombre, cargo, contacto)
   - 📅 Fechas (inicio y fin - mínimo 3 meses)
   - 📊 Área de práctica
   - ⏰ Horas totales (mínimo 480 horas)
   - 📍 Modalidad (PRESENCIAL, REMOTO, HÍBRIDO)
3. Carga documentos requeridos:
   - ✅ Carta de presentación (universidad)
   - ✅ Carta de aceptación (empresa)
   - ✅ Plan de trabajo detallado
   - ✅ Convenio marco (si aplica)
4. **Acción**: `submit()` → Estado: `PENDING`

### Fase 2: Validación 🔍 (SECRETARIA)

**Duración**: 2-3 días

1. **Secretaria** revisa documentos cargados
2. Valida datos de la empresa:
   - ✅ RUC válido de 11 dígitos
   - ✅ Razón social correcta
   - ✅ Datos de contacto completos
   - ✅ Estado de empresa: ACTIVE
3. Verifica elegibilidad del estudiante:
   - ✅ Semestre mínimo: 6to
   - ✅ Promedio ponderado mínimo: 12.0
   - ✅ Código de estudiante válido
   - ✅ Sin prácticas activas previas
4. **Resultado**:
   - ✅ Aprueba documentos → Notifica COORDINADOR
   - ❌ Rechaza → Solicita correcciones al ESTUDIANTE

### Fase 3: Aprobación 👨‍🏫 (COORDINADOR)

**Duración**: 3-5 días

1. **Coordinador** revisa la solicitud (`PENDING`)
2. Verifica requisitos académicos:
   - ✅ Currículo completo
   - ✅ Cumplimiento de pre-requisitos
   - ✅ Disponibilidad de horario
3. Valida condiciones de práctica:
   - ✅ Duración mínima: 480 horas
   - ✅ Duración mínima: 90 días (3 meses)
   - ✅ Supervisor empresarial competente
   - ✅ Objetivos de aprendizaje claros
4. **Decisión**:
   - ✅ **Aprobar** → Estado: `APPROVED`
     - Asigna supervisor (si es necesario)
     - Notifica a estudiante y supervisor
   - ❌ **Rechazar** → Estado: `CANCELLED`
     - Registra observaciones
     - Notifica al estudiante

### Fase 4: Ejecución 🚀 (ESTUDIANTE + SUPERVISOR)

**Duración**: 3-6 meses (según plan)

#### Inicio de Práctica

1. **Estudiante** inicia la práctica → Estado: `IN_PROGRESS`
2. Se activa el tracking de:
   - ⏰ Horas trabajadas
   - 📋 Actividades realizadas
   - 📊 Progreso semanal/mensual

#### Durante la Práctica

**Responsabilidades del ESTUDIANTE**:
- 📝 Registra horas trabajadas diarias
- 📋 Documenta actividades realizadas
- 📄 Sube informes mensuales/bimestrales:
  - Informe Mes 1 (20% completado)
  - Informe Mes 2 (40% completado)
  - Informe Mes 3 (60% completado)
  - Informe Final (100% completado)
- 📊 Mantiene bitácora actualizada
- 💬 Responde evaluaciones de supervisor

**Responsabilidades del SUPERVISOR**:
- ✅ Aprueba/rechaza informes mensuales
- 📊 Evalúa desempeño del practicante
- ⏰ Valida horas registradas
- 📝 Registra observaciones
- 🎯 Guía en cumplimiento de objetivos

#### Indicadores de Progreso

| Métrica | Descripción | Mínimo Requerido |
|---------|-------------|------------------|
| Horas Completadas | Horas trabajadas acumuladas | 480 horas |
| Progreso (%) | (Horas completadas / Horas totales) × 100 | 100% |
| Informes Aprobados | Informes mensuales validados | Todos |
| Evaluación Supervisor | Calificación promedio | ≥ 14.0 |
| Asistencia (%) | Días asistidos / Días programados | ≥ 90% |

### Fase 5: Finalización 🎓 (COORDINADOR)

**Duración**: 5-7 días

1. Estudiante completa **480 horas mínimas** → 100% progreso
2. Sube **informe final** completo:
   - Resumen ejecutivo
   - Objetivos cumplidos
   - Aprendizajes obtenidos
   - Conclusiones y recomendaciones
   - Evidencias (fotos, documentos)
3. **Supervisor** emite evaluación final
4. **Coordinador** revisa:
   - ✅ Cumplimiento de horas
   - ✅ Calidad de informes
   - ✅ Evaluación de supervisor
   - ✅ Objetivos cumplidos
5. **Coordinador** asigna **calificación final** (0-20)
6. **Acción**: `complete()` → Estado: `COMPLETED`
7. Sistema genera **certificado oficial** automáticamente

#### Certificado de Práctica

**Formato**: PDF oficial con firma digital

**Contenido**:
- 🎓 Datos del estudiante (código, nombre, carrera)
- 🏢 Datos de la empresa (RUC, razón social, sector)
- 👔 Datos del supervisor (nombre, cargo)
- 📅 Periodo de práctica (fechas inicio/fin)
- ⏰ Horas completadas
- 📊 Calificación final (0-20)
- 🔢 Número de certificado único: `CERT-XXXXXX-YYYY`
- 📅 Fecha de emisión
- ✍️ Firma coordinador

---

## 🔐 Matriz de Permisos Detallada por Rol

### 1️⃣ PRACTICANTE (Estudiante)

**Nivel de Acceso**: Básico (Solo recursos propios)

| Recurso | Crear | Listar | Ver | Editar | Eliminar | Condiciones |
|---------|-------|--------|-----|--------|----------|-------------|
| **Users** | ❌ | ❌ | ✅ | ✅ | ❌ | Solo perfil propio |
| **Students** | ❌ | ❌ | ✅ | ✅ | ❌ | Solo perfil propio |
| **Companies** | ❌ | ✅ | ✅ | ❌ | ❌ | Solo ACTIVE |
| **Supervisors** | ❌ | ✅ | ✅ | ❌ | ❌ | Solo información |
| **Practices** | ✅ | ✅ | ✅ | ✅ | ❌ | Propias / Solo DRAFT |
| **Documents** | ✅ | ✅ | ✅ | ❌ | ✅ | Propios / No aprobados |
| **Notifications** | ❌ | ✅ | ✅ | ✅ | ❌ | Propias / Marcar leídas |

**Acciones Permitidas**:
- ✅ Crear nueva práctica
- ✅ Ver sus prácticas
- ✅ Editar práctica en estado DRAFT
- ✅ Enviar práctica a revisión (DRAFT → PENDING)
- ✅ Iniciar práctica aprobada (APPROVED → IN_PROGRESS)
- ✅ Subir documentos (informes, evidencias)
- ✅ Registrar horas trabajadas
- ✅ Ver notificaciones
- ❌ Aprobar prácticas
- ❌ Calificar
- ❌ Ver otras prácticas

### 2️⃣ SUPERVISOR (Empresa)

**Nivel de Acceso**: Limitado a prácticas asignadas

| Recurso | Crear | Listar | Ver | Editar | Eliminar | Condiciones |
|---------|-------|--------|-----|--------|----------|-------------|
| **Users** | ❌ | ❌ | ✅ | ✅ | ❌ | Solo perfil propio |
| **Students** | ❌ | ✅ | ✅ | ❌ | ❌ | Solo asignados |
| **Companies** | ❌ | ❌ | ✅ | ✅ | ❌ | Solo empresa propia |
| **Supervisors** | ❌ | ❌ | ✅ | ✅ | ❌ | Solo perfil propio |
| **Practices** | ❌ | ✅ | ✅ | ✅ | ❌ | Solo asignadas |
| **Documents** | ❌ | ✅ | ✅ | ❌ | ❌ | De prácticas asignadas |
| **Notifications** | ❌ | ✅ | ✅ | ✅ | ❌ | Propias |

**Acciones Permitidas**:
- ✅ Ver prácticas asignadas
- ✅ Evaluar desempeño de practicantes
- ✅ Aprobar/rechazar informes
- ✅ Registrar horas trabajadas
- ✅ Agregar observaciones
- ✅ Ver documentos de practicantes
- ✅ Calificar desempeño mensual
- ❌ Crear prácticas
- ❌ Aprobar prácticas
- ❌ Ver otras empresas
- ❌ Completar prácticas

### 3️⃣ SECRETARIA (Administrativa)

**Nivel de Acceso**: Gestión administrativa completa

| Recurso | Crear | Listar | Ver | Editar | Eliminar | Condiciones |
|---------|-------|--------|-----|--------|----------|-------------|
| **Users** | ❌ | ✅ | ✅ | ✅ | ❌ | Todos |
| **Students** | ❌ | ✅ | ✅ | ✅ | ❌ | Todos |
| **Companies** | ✅ | ✅ | ✅ | ✅ | ❌ | Todas |
| **Supervisors** | ✅ | ✅ | ✅ | ✅ | ❌ | Todos |
| **Practices** | ❌ | ✅ | ✅ | ✅ | ❌ | Todas / Datos básicos |
| **Documents** | ✅ | ✅ | ✅ | ✅ | ✅ | Todos / Validación |
| **Notifications** | ✅ | ✅ | ✅ | ✅ | ❌ | Todas |

**Acciones Permitidas**:
- ✅ Ver todas las prácticas
- ✅ Editar datos básicos de prácticas
- ✅ Validar documentos (aprobar/rechazar)
- ✅ Gestionar empresas (crear, editar)
- ✅ Gestionar supervisores
- ✅ Editar información de estudiantes
- ✅ Crear notificaciones
- ✅ Generar reportes básicos
- ⚠️ Aprobar prácticas (solo validación inicial)
- ❌ Calificar prácticas
- ❌ Completar prácticas

### 4️⃣ COORDINADOR (Académico)

**Nivel de Acceso**: Control académico completo

| Recurso | Crear | Listar | Ver | Editar | Eliminar | Condiciones |
|---------|-------|--------|-----|--------|----------|-------------|
| **Users** | ✅ | ✅ | ✅ | ✅ | ❌ | Todos |
| **Students** | ✅ | ✅ | ✅ | ✅ | ❌ | Todos |
| **Companies** | ✅ | ✅ | ✅ | ✅ | ✅ | Todas |
| **Supervisors** | ✅ | ✅ | ✅ | ✅ | ✅ | Todos |
| **Practices** | ✅ | ✅ | ✅ | ✅ | ✅ | Todas |
| **Documents** | ✅ | ✅ | ✅ | ✅ | ✅ | Todos |
| **Notifications** | ✅ | ✅ | ✅ | ✅ | ✅ | Todas |
| **Reports** | ✅ | ✅ | ✅ | ❌ | ❌ | Todos |
| **Statistics** | ❌ | ✅ | ✅ | ❌ | ❌ | Todas |

**Acciones Permitidas**:
- ✅ Ver todas las prácticas
- ✅ Aprobar/rechazar prácticas (PENDING → APPROVED/CANCELLED)
- ✅ Asignar supervisores a prácticas
- ✅ Completar prácticas (IN_PROGRESS → COMPLETED)
- ✅ Calificar prácticas (nota 0-20)
- ✅ Cancelar/suspender prácticas
- ✅ Gestionar estudiantes completa
- ✅ Gestionar empresas completa
- ✅ Generar reportes avanzados
- ✅ Ver estadísticas globales
- ✅ Exportar datos (Excel, CSV, PDF)
- ✅ Crear/editar usuarios
- ✅ Validar documentos

### 5️⃣ ADMINISTRADOR (Sistema)

**Nivel de Acceso**: Total (sin restricciones)

| Recurso | Crear | Listar | Ver | Editar | Eliminar | Condiciones |
|---------|-------|--------|-----|--------|----------|-------------|
| **TODO** | ✅ | ✅ | ✅ | ✅ | ✅ | Sin restricciones |

**Acciones Permitidas**:
- ✅ **Acceso total** al sistema
- ✅ Gestionar usuarios y roles
- ✅ Asignar/revocar permisos personalizados
- ✅ Configuración del sistema
- ✅ Ver logs de auditoría
- ✅ Gestionar backups
- ✅ Migración de datos
- ✅ Acceso a Django Admin
- ✅ Ejecutar comandos de management
- ✅ Ver métricas del sistema

---

## 📋 Requisitos y Validaciones del Sistema

### Para Estudiantes (PRACTICANTE)

| Requisito | Validación | Valor Mínimo | Crítico |
|-----------|------------|--------------|---------|
| Semestre Académico | ≥ 6to semestre | 6 | ✅ |
| Promedio Ponderado | ≥ 12.0 | 12.0 | ✅ |
| Código Estudiante | Formato válido `YYYY######` | - | ✅ |
| Currículo | CV actualizado | - | ✅ |
| Prácticas Activas | Sin prácticas en progreso | 0 | ✅ |
| Créditos Aprobados | Según carrera | Variable | ⚠️ |
| Estado Académico | Regular / No está con deuda | - | ✅ |

### Para Empresas

| Requisito | Validación | Formato | Crítico |
|-----------|------------|---------|---------|
| RUC | Válido Perú | 11 dígitos numéricos | ✅ |
| Razón Social | Completa y correcta | - | ✅ |
| Estado | ACTIVE (validada) | - | ✅ |
| Dirección | Completa y verificable | - | ✅ |
| Contacto | Teléfono y email | Válidos | ✅ |
| Sector Económico | Definido | - | ⚠️ |
| Tamaño Empresa | MICRO, PEQUEÑA, MEDIANA, GRANDE | - | ⚠️ |

### Para Supervisores

| Requisito | Validación | Descripción | Crítico |
|-----------|------------|-------------|---------|
| Nombre Completo | Obligatorio | - | ✅ |
| Cargo | Debe estar definido | - | ✅ |
| Email Corporativo | Válido y activo | - | ✅ |
| Teléfono | Contacto directo | - | ✅ |
| Experiencia | Mínimo 2 años en área | - | ⚠️ |
| Empresa Asociada | Debe existir y estar ACTIVE | - | ✅ |

### Para Prácticas

| Requisito | Validación | Valor Mínimo | Crítico |
|-----------|------------|--------------|---------|
| Duración (Horas) | ≥ 480 horas | 480 | ✅ |
| Duración (Días) | ≥ 90 días (3 meses) | 90 | ✅ |
| Supervisor | Asignado y activo | 1 | ✅ |
| Documentación | Completa | 4 docs mín. | ✅ |
| Área Definida | Coherente con carrera | - | ✅ |
| Objetivos | Mínimo 3 objetivos | 3 | ✅ |
| Fecha Fin > Fecha Inicio | Lógica temporal | - | ✅ |
| Modalidad | PRESENCIAL, REMOTO, HÍBRIDO | - | ✅ |

### Documentos Requeridos

| Documento | Emisor | Formato | Obligatorio | Validado Por |
|-----------|--------|---------|-------------|--------------|
| Carta de Presentación | Universidad | PDF | ✅ | SECRETARIA |
| Carta de Aceptación | Empresa | PDF | ✅ | SECRETARIA |
| Plan de Trabajo | Estudiante | PDF | ✅ | COORDINADOR |
| Convenio Marco | Universidad/Empresa | PDF | ⚠️ | SECRETARIA |
| Informe Mensual 1 | Estudiante | PDF | ✅ | SUPERVISOR |
| Informe Mensual 2 | Estudiante | PDF | ✅ | SUPERVISOR |
| Informe Mensual 3 | Estudiante | PDF | ✅ | SUPERVISOR |
| Informe Final | Estudiante | PDF | ✅ | COORDINADOR |

---

## 📊 Indicadores Clave de Desempeño (KPIs)

### Indicadores Operativos

| KPI | Fórmula | Meta | Frecuencia |
|-----|---------|------|------------|
| **Progreso de Horas** | (Horas completadas / Horas totales) × 100 | 100% | Diaria |
| **Tasa de Aprobación** | (Prácticas aprobadas / Solicitadas) × 100 | ≥ 85% | Mensual |
| **Tiempo Promedio de Aprobación** | Promedio días (PENDING → APPROVED) | ≤ 5 días | Mensual |
| **Tasa de Completación** | (Prácticas completadas / Iniciadas) × 100 | ≥ 90% | Semestral |
| **Calificación Promedio** | Promedio de notas finales | ≥ 15.0 | Semestral |
| **Prácticas Activas** | Count(status=IN_PROGRESS) | - | Diaria |
| **Empresas Activas** | Count(companies con practicantes) | - | Mensual |

### Indicadores de Calidad

| KPI | Descripción | Meta | Seguimiento |
|-----|-------------|------|-------------|
| **Satisfacción Estudiante** | Encuesta post-práctica (1-5) | ≥ 4.0 | Al completar |
| **Satisfacción Empresa** | Encuesta a supervisor (1-5) | ≥ 4.0 | Al completar |
| **Documentos Aprobados 1ra vez** | % docs aprobados sin corrección | ≥ 70% | Mensual |
| **Asistencia Promedio** | % asistencia de practicantes | ≥ 95% | Semanal |
| **Tiempo Respuesta Supervisor** | Días para evaluar informe | ≤ 3 días | Semanal |

### Indicadores Administrativos

| KPI | Descripción | Meta | Frecuencia |
|-----|-------------|------|------------|
| **Prácticas Pendientes** | Count(status=PENDING) | ≤ 10 | Diaria |
| **Documentos Sin Validar** | Count(docs sin aprobar) | ≤ 5 | Diaria |
| **Notificaciones No Leídas** | Count(notif no leídas) | - | Diaria |
| **Empresas Nuevas** | Count(nuevas/mes) | - | Mensual |
| **Tasa de Rechazo** | (Rechazadas / Total) × 100 | ≤ 10% | Mensual |

---

## 🔔 Sistema de Notificaciones

### Eventos que Generan Notificaciones

| Evento | Destinatarios | Tipo | Prioridad | Canal |
|--------|---------------|------|-----------|-------|
| **Práctica creada** | COORDINADOR, SECRETARIA | INFO | Media | Email + Sistema |
| **Práctica enviada a revisión** | COORDINADOR | INFO | Alta | Email + Sistema |
| **Práctica aprobada** | PRACTICANTE | SUCCESS | Alta | Email + Sistema |
| **Práctica rechazada** | PRACTICANTE | WARNING | Alta | Email + Sistema |
| **Práctica iniciada** | PRACTICANTE, SUPERVISOR | INFO | Media | Email + Sistema |
| **Documento subido** | COORDINADOR, SUPERVISOR | INFO | Media | Sistema |
| **Documento aprobado** | PRACTICANTE | SUCCESS | Media | Sistema |
| **Documento rechazado** | PRACTICANTE | WARNING | Alta | Email + Sistema |
| **Informe pendiente** | PRACTICANTE | WARNING | Alta | Email + Sistema |
| **Informe vencido** | PRACTICANTE, COORDINADOR | ALERT | Crítica | Email + SMS |
| **Práctica completada** | PRACTICANTE | SUCCESS | Alta | Email + Sistema |
| **Práctica suspendida** | PRACTICANTE, SUPERVISOR | ALERT | Crítica | Email + Sistema |
| **Horas meta alcanzada** | PRACTICANTE | SUCCESS | Media | Sistema |
| **Calificación asignada** | PRACTICANTE | INFO | Alta | Email + Sistema |
| **Certificado generado** | PRACTICANTE | SUCCESS | Alta | Email |

### Tipos de Notificaciones

| Tipo | Color | Icono | Descripción | Duración |
|------|-------|-------|-------------|----------|
| **INFO** | 🔵 Azul | ℹ️ | Información general | 7 días |
| **SUCCESS** | 🟢 Verde | ✅ | Acción exitosa | 14 días |
| **WARNING** | 🟡 Amarillo | ⚠️ | Advertencia | 30 días |
| **ALERT** | 🔴 Rojo | 🚨 | Urgente/Crítico | 60 días |
| **ERROR** | 🔴 Rojo | ❌ | Error del sistema | 90 días |

---

## 📈 Reportes y Analytics Disponibles

### Reportes para COORDINADOR

| Reporte | Descripción | Filtros | Formato | Frecuencia |
|---------|-------------|---------|---------|------------|
| **Reporte de Prácticas** | Todas las prácticas | Estado, Fechas, Carrera | PDF, Excel, CSV | On-demand |
| **Reporte de Estudiantes** | Estudiantes y sus prácticas | Carrera, Semestre, Promedio | PDF, Excel | Mensual |
| **Reporte de Empresas** | Empresas y practicantes | Sector, Tamaño, Ubicación | PDF, Excel | Mensual |
| **Dashboard Global** | Estadísticas generales | Periodo | Web | Tiempo real |
| **Análisis de Desempeño** | KPIs y métricas | Periodo | PDF | Mensual |
| **Reporte de Calificaciones** | Notas y promedios | Periodo, Carrera | Excel | Semestral |

### Reportes para SUPERVISOR

| Reporte | Descripción | Filtros | Formato | Frecuencia |
|---------|-------------|---------|---------|------------|
| **Mis Practicantes** | Practicantes asignados | Estado | PDF, Web | Diaria |
| **Evaluaciones Pendientes** | Informes por evaluar | - | Web | Diaria |
| **Historial de Evaluaciones** | Evaluaciones realizadas | Periodo | PDF | Mensual |
| **Progreso de Horas** | Avance de cada practicante | - | Web | Semanal |

### Reportes para PRACTICANTE

| Reporte | Descripción | Filtros | Formato | Frecuencia |
|---------|-------------|---------|---------|------------|
| **Mi Progreso** | Estado actual de práctica | - | Web | Tiempo real |
| **Historial de Horas** | Registro de horas trabajadas | Periodo | PDF, Excel | On-demand |
| **Mis Documentos** | Documentos subidos | Estado | Web | Diaria |
| **Certificado de Práctica** | Documento oficial | - | PDF | Al completar |

### Gráficas Disponibles (Chart.js)

1. **Prácticas por Estado** (Pie/Donut Chart)
2. **Estudiantes por Carrera** (Bar Chart)
3. **Empresas por Sector** (Bar Chart)
4. **Línea Temporal** (Line Chart)
5. **Progreso de Horas** (Progress Bar)
6. **Calificaciones** (Histogram)

---

## 🛡️ Seguridad del Sistema

### Autenticación

- **Método**: JWT (JSON Web Tokens)
- **Duración Access Token**: 1 hora
- **Duración Refresh Token**: 7 días
- **Algoritmo**: HS256
- **Blacklist**: Redis para tokens revocados

### Autorización (RBAC)

- **Control**: Role-Based Access Control
- **Granularidad**: Por recurso y acción
- **Herencia**: Jerarquía de roles
- **Override**: Permisos personalizados por usuario

### Protecciones Implementadas

| Protección | Tecnología | Descripción |
|------------|-----------|-------------|
| **Rate Limiting** | django-ratelimit | 100 req/min por IP |
| **CORS** | django-cors-headers | Orígenes permitidos |
| **SQL Injection** | Django ORM | Queries parametrizadas |
| **XSS** | DRF + Bleach | Sanitización de inputs |
| **CSRF** | Django CSRF | Tokens en forms |
| **Brute Force** | django-axes | Max 5 intentos login |
| **Auditoría** | Logs personalizados | Todos los cambios |

### Logging y Auditoría

```python
# Eventos registrados:
- LOGIN_SUCCESS / LOGIN_FAILED
- PRACTICE_CREATED / PRACTICE_UPDATED
- PRACTICE_STATUS_CHANGED
- DOCUMENT_UPLOADED / DOCUMENT_APPROVED
- USER_CREATED / USER_UPDATED
- PERMISSION_GRANTED / PERMISSION_REVOKED
```

### Encriptación

- **Passwords**: Argon2 (Django default)
- **Datos sensibles**: AES-256
- **Conexiones**: TLS 1.3
- **Base de datos**: Columnas sensibles encriptadas

---

## 🎯 Stack Tecnológico

### Backend

| Tecnología | Versión | Propósito |
|-----------|---------|-----------|
| **Python** | 3.11+ | Lenguaje base |
| **Django** | 5.0+ | Framework web |
| **Django REST Framework** | 3.15+ | API REST |
| **Graphene-Django** | 3.2+ | API GraphQL |
| **Django Scalar** | 0.2+ | Documentación interactiva |

### Bases de Datos

| BD | Propósito | Proveedor |
|----|-----------|-----------|
| **PostgreSQL** | Datos transaccionales | Azure Database |
| **Redis** | Caché + Celery | Azure Cache |
| **MongoDB/CosmosDB** | Documentos + Logs | Azure CosmosDB |

### Tareas Asíncronas

| Tecnología | Propósito |
|-----------|-----------|
| **Celery** | Procesamiento asíncrono |
| **Redis** | Message broker |
| **Celery Beat** | Tareas programadas |

### Infraestructura

| Servicio | Proveedor | Descripción |
|----------|-----------|-------------|
| **App Service** | Azure | Hosting Django |
| **PostgreSQL** | Azure | Base de datos |
| **Redis Cache** | Azure | Caché y broker |
| **CosmosDB** | Azure | Documentos |
| **Application Insights** | Azure | Monitoreo |
| **Blob Storage** | Azure | Archivos estáticos |

### Testing

| Framework | Cobertura | Tipos |
|-----------|-----------|-------|
| **Pytest** | > 80% | Unit, Integration |
| **Pytest-Django** | - | Django-specific |
| **Factory Boy** | - | Test fixtures |
| **Faker** | - | Datos de prueba |

---

## 📐 Arquitectura del Sistema

### Patrón: Arquitectura Hexagonal (Ports & Adapters)

```
┌─────────────────────────────────────────────────────┐
│                   Presentación                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  REST API    │  │  GraphQL     │  │  Scalar   │ │
│  │  (DRF)       │  │  (Graphene)  │  │  (Docs)   │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                  Aplicación                         │
│  ┌──────────────────────────────────────────────┐  │
│  │          Use Cases (Casos de Uso)            │  │
│  │  - CreatePracticeUseCase                     │  │
│  │  - UpdatePracticeStatusUseCase               │  │
│  │  - ApprovePracticeUseCase                    │  │
│  └──────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                    Dominio                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  Entities    │  │ Value Objects│  │   Enums   │ │
│  │  - User      │  │ - Calificacion│  │ - Status  │ │
│  │  - Practice  │  │ - Periodo    │  │ - Role    │ │
│  │  - Student   │  │              │  │           │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                   Puertos                           │
│  ┌──────────────────────────────────────────────┐  │
│  │      Repository Ports (Interfaces)           │  │
│  │  - PracticeRepositoryPort                    │  │
│  │  - StudentRepositoryPort                     │  │
│  └──────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                 Adaptadores                         │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  PostgreSQL  │  │    Redis     │  │  MongoDB  │ │
│  │  (ORM)       │  │   (Cache)    │  │  (Docs)   │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
```

### Capas y Responsabilidades

| Capa | Responsabilidad | Tecnologías |
|------|----------------|-------------|
| **Presentación** | Interfaz con cliente | DRF, GraphQL, Scalar |
| **Aplicación** | Orquestación de casos de uso | Python, DTOs |
| **Dominio** | Lógica de negocio pura | Entities, Value Objects |
| **Puertos** | Contratos/Interfaces | Abstract Base Classes |
| **Adaptadores** | Implementaciones concretas | Django ORM, Redis, MongoDB |

---

## 🚀 Endpoints Disponibles

### REST API (126 endpoints)

**Base URL**: `/api/v2/`

#### Autenticación
```
POST   /api/v2/auth/login/           - Login con JWT
POST   /api/v2/auth/register/        - Registro
POST   /api/v2/auth/refresh/         - Refresh token
POST   /api/v2/auth/logout/          - Logout
```

#### Prácticas
```
GET    /api/v2/practices/            - Listar
POST   /api/v2/practices/            - Crear
GET    /api/v2/practices/{id}/       - Ver detalle
PUT    /api/v2/practices/{id}/       - Actualizar
DELETE /api/v2/practices/{id}/       - Eliminar
POST   /api/v2/practices/{id}/submit/     - Enviar a revisión
POST   /api/v2/practices/{id}/approve/    - Aprobar
POST   /api/v2/practices/{id}/reject/     - Rechazar
POST   /api/v2/practices/{id}/start/      - Iniciar
POST   /api/v2/practices/{id}/complete/   - Completar
GET    /api/v2/practices/by_status/       - Por estado
```

#### Dashboards
```
GET    /api/v2/dashboards/coordinator/    - Dashboard coordinador
GET    /api/v2/dashboards/supervisor/     - Dashboard supervisor
GET    /api/v2/dashboards/student/        - Dashboard estudiante
GET    /api/v2/dashboards/charts/         - Datos para gráficas
```

#### Reportes
```
GET    /api/v2/reports/practices/         - Reporte prácticas
GET    /api/v2/reports/students/          - Reporte estudiantes
GET    /api/v2/reports/{id}/certificate/  - Certificado PDF
```

### GraphQL API (80 queries/mutations)

**Endpoint**: `/graphql/`

#### Queries
```graphql
query {
  allPractices { ... }
  myPractices { ... }
  practicesByStatus(status: "PENDING") { ... }
  allStudents { ... }
  allCompanies { ... }
}
```

#### Mutations
```graphql
mutation {
  createPractice(input: {...}) { ... }
  submitPractice(practiceId: "1") { ... }
  approvePractice(practiceId: "1") { ... }
  startPractice(practiceId: "1") { ... }
  completePractice(practiceId: "1") { ... }
}
```

### Scalar/Swagger

**Endpoints**:
- `/api/schema/` - OpenAPI Schema
- `/api/docs/` - Scalar UI
- `/api/swagger/` - Swagger UI

---

## 📊 Casos de Uso Principales

### 1. Registrar Nueva Práctica

**Actor**: PRACTICANTE

**Flujo**:
1. Estudiante accede al sistema
2. Completa formulario de práctica
3. Sube documentos requeridos
4. Envía a revisión
5. Sistema notifica a COORDINADOR

**Validaciones**:
- Semestre ≥ 6to
- Promedio ≥ 12.0
- Horas ≥ 480
- Duración ≥ 90 días

### 2. Aprobar Práctica

**Actor**: COORDINADOR

**Flujo**:
1. Coordinador revisa solicitud PENDING
2. Valida documentos y requisitos
3. Asigna supervisor (opcional)
4. Aprueba práctica
5. Sistema notifica a ESTUDIANTE

**Validaciones**:
- Estado = PENDING
- Documentos completos
- Empresa ACTIVE

### 3. Completar Práctica

**Actor**: COORDINADOR

**Flujo**:
1. Estudiante completa 480 horas
2. Sube informe final
3. Supervisor evalúa
4. Coordinador revisa y califica
5. Sistema marca como COMPLETED
6. Genera certificado automático

**Validaciones**:
- Horas completadas = 100%
- Estado = IN_PROGRESS
- Informes aprobados
- Calificación 0-20

---

## 🎯 Beneficios del Sistema

### Para Estudiantes
- ✅ Proceso digitalizado y transparente
- ✅ Seguimiento en tiempo real
- ✅ Notificaciones automáticas
- ✅ Certificado digital al finalizar
- ✅ Historial completo de prácticas

### Para Supervisores
- ✅ Gestión simplificada de practicantes
- ✅ Evaluación en línea
- ✅ Dashboard personalizado
- ✅ Comunicación directa

### Para Coordinadores
- ✅ Control total del proceso
- ✅ Reportes y estadísticas
- ✅ Toma de decisiones basada en datos
- ✅ Automatización de tareas
- ✅ Auditoría completa

### Para la Institución
- ✅ Trazabilidad total
- ✅ Cumplimiento normativo
- ✅ Base de datos de empresas
- ✅ Métricas de calidad
- ✅ Reducción de tiempos administrativos

---

## 📝 Conclusión

Este sistema garantiza:

- ✅ **Trazabilidad Completa**: Historial de todos los cambios
- ✅ **Seguridad por Roles**: RBAC con 5 niveles
- ✅ **Flujos Validados**: Máquina de estados robusta
- ✅ **Escalabilidad**: Arquitectura hexagonal
- ✅ **Auditoría**: Logging de eventos críticos
- ✅ **Automatización**: Notificaciones y certificados
- ✅ **Calidad**: Testing > 80% cobertura

---

**Sistema de Gestión de Prácticas Profesionales v2.0**  
Universidad Peruana Unión  
Última actualización: Octubre 2025
