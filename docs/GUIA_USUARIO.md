# 👥 Guía de Usuario - Sistema de Gestión de Prácticas Profesionales

## 📋 Tabla de Contenidos

- [Introducción](#introducción)
- [Roles del Sistema](#roles-del-sistema)
- [Guía por Rol](#guía-por-rol)
  - [Estudiante (Practicante)](#estudiante-practicante)
  - [Supervisor de Empresa](#supervisor-de-empresa)
  - [Coordinador Académico](#coordinador-académico)
  - [Secretaria](#secretaria)
  - [Administrador](#administrador)
- [Procesos Principales](#procesos-principales)
- [Preguntas Frecuentes](#preguntas-frecuentes)

---

## 🎯 Introducción

El Sistema de Gestión de Prácticas Profesionales es una plataforma integral que facilita la administración del proceso completo de prácticas pre-profesionales, desde el registro de empresas hasta la emisión de certificados.

### Características Principales

✅ **Gestión de Prácticas**: Registro, seguimiento y evaluación  
✅ **Documentos Digitales**: Carga y validación de documentos  
✅ **Notificaciones**: Alertas automáticas por email  
✅ **Reportes**: Estadísticas y métricas en tiempo real  
✅ **Dashboard Personalizado**: Por cada rol de usuario  
✅ **Trazabilidad**: Auditoría completa de acciones

---

## 👤 Roles del Sistema

### 1. **PRACTICANTE** (Estudiante)
- Registrar solicitud de prácticas
- Cargar documentos requeridos
- Ver progreso de horas
- Recibir notificaciones
- Descargar certificado

### 2. **SUPERVISOR** (Empresa)
- Evaluar practicantes
- Registrar horas trabajadas
- Aprobar/rechazar documentos
- Ver informes de desempeño

### 3. **COORDINADOR** (Académico)
- Aprobar solicitudes de prácticas
- Asignar supervisores
- Ver estadísticas globales
- Generar reportes

### 4. **SECRETARIA** (Administrativa)
- Validar documentos
- Registrar empresas
- Gestionar estudiantes
- Aprobar solicitudes iniciales

### 5. **ADMINISTRADOR** (Sistema)
- Configuración global
- Gestión de usuarios
- Respaldos del sistema
- Auditoría de seguridad

---

## 📖 Guía por Rol

## 🎓 Estudiante (Practicante)

### 1. Registro e Inicio de Sesión

#### Primer Acceso

1. Accede a: `http://sistema.upeu.edu.pe`
2. Haz clic en **"Registrarse"**
3. Completa el formulario:
   - Email institucional (@upeu.edu.pe)
   - Código de estudiante
   - Nombre completo
   - Contraseña segura
4. Verifica tu email (revisa bandeja de entrada y spam)
5. Inicia sesión con tus credenciales

### 2. Dashboard Estudiantil

Al iniciar sesión verás:

```
┌─────────────────────────────────────────────┐
│  👤 Bienvenido, Juan Pérez                  │
├─────────────────────────────────────────────┤
│  📊 Mi Dashboard                            │
│                                             │
│  🎯 Práctica Actual                         │
│  • Empresa: TechCorp SAC                    │
│  • Inicio: 01/03/2024                       │
│  • Progreso: 320/480 horas (66.7%)          │
│                                             │
│  📄 Documentos Pendientes (2)               │
│  • Plan de Trabajo - Pendiente              │
│  • Informe Mensual 1 - Aprobado ✓           │
│                                             │
│  🔔 Notificaciones (3)                      │
│  • Supervisor aprobó tu informe             │
│  • Nueva tarea asignada                     │
└─────────────────────────────────────────────┘
```

### 3. Solicitar Práctica

#### Paso 1: Nueva Solicitud

1. Dashboard → **"Nueva Práctica"**
2. Completa información:
   - Empresa (buscar o registrar nueva)
   - Área de práctica
   - Fecha de inicio
   - Duración esperada (480 horas mínimo)

#### Paso 2: Cargar Documentos

Documentos requeridos:
- ✅ Carta de presentación (de la universidad)
- ✅ Carta de aceptación (de la empresa)
- ✅ Plan de trabajo
- ✅ Convenio (si aplica)

Para cada documento:
1. Clic en **"Cargar Documento"**
2. Seleccionar tipo
3. Adjuntar archivo PDF (máx 5MB)
4. Agregar descripción
5. **"Enviar"**

#### Paso 3: Seguimiento

Estados de la solicitud:
- 🟡 **DRAFT**: En borrador (puedes editar)
- 🟠 **PENDING**: En revisión por secretaría
- 🔵 **APPROVED**: Aprobado por coordinador
- 🟢 **IN_PROGRESS**: Práctica en curso
- ✅ **COMPLETED**: Práctica finalizada

### 4. Durante la Práctica

#### Registrar Actividades

1. Dashboard → **"Mis Actividades"**
2. **"Nueva Actividad"**
3. Completa:
   - Fecha
   - Horas trabajadas
   - Descripción de actividades
   - Competencias desarrolladas
4. **"Guardar"**

#### Cargar Informes

**Informes Mensuales**:
- Obligatorios cada mes
- Formato: Plantilla oficial
- Debe incluir: actividades, horas, logros
- Aprobación requerida del supervisor

1. Dashboard → **"Informes"**
2. **"Nuevo Informe Mensual"**
3. Completar plantilla
4. Adjuntar evidencias (fotos, capturas)
5. **"Enviar a Supervisor"**

### 5. Finalizar Práctica

#### Requisitos

- ✅ 480 horas completadas mínimo
- ✅ Todos los informes mensuales aprobados
- ✅ Informe final aprobado
- ✅ Evaluación del supervisor (nota ≥ 12.0)
- ✅ Constancia de la empresa

#### Proceso

1. Dashboard → **"Finalizar Práctica"**
2. Cargar **Informe Final** (completo)
3. Cargar **Constancia de Prácticas** (empresa)
4. Cargar **Evaluación Final** (firmada)
5. Esperar aprobación del coordinador
6. Descargar **Certificado**

### 6. Descargar Certificado

Una vez aprobado:

1. Dashboard → **"Mi Certificado"**
2. **"Descargar PDF"**
3. El certificado incluye:
   - Número único de certificado
   - Datos del estudiante
   - Datos de la empresa
   - Horas completadas
   - Periodo de prácticas
   - Firma digital del coordinador

---

## 👔 Supervisor de Empresa

### 1. Acceso al Sistema

Recibirás un email de invitación:
- Usuario: tu email corporativo
- Contraseña temporal (cámbiala en primer acceso)

### 2. Dashboard del Supervisor

```
┌─────────────────────────────────────────────┐
│  👔 Bienvenido, Carlos Ruiz (Supervisor)    │
├─────────────────────────────────────────────┤
│  📊 Mis Practicantes (5)                    │
│                                             │
│  🟢 Activos: 3                              │
│  • Juan Pérez - 320/480 hrs (66%)           │
│  • María López - 450/480 hrs (94%)          │
│  • Pedro Sánchez - 200/480 hrs (42%)        │
│                                             │
│  📋 Pendientes de Evaluación (2)            │
│  • Informe Mensual - Juan Pérez             │
│  • Informe Final - María López              │
│                                             │
│  📊 Rendimiento Promedio: 16.2/20           │
└─────────────────────────────────────────────┘
```

### 3. Evaluar Informes

1. Dashboard → **"Informes Pendientes"**
2. Seleccionar informe
3. Revisar contenido
4. Completar evaluación:
   - **Nota** (0-20)
   - **Comentarios** (feedback detallado)
   - **Estado**: Aprobado / Observado / Rechazado
5. **"Enviar Evaluación"**

### 4. Registrar Horas

1. Dashboard → **"Practicantes"**
2. Seleccionar estudiante
3. **"Registrar Horas"**
4. Ingresar:
   - Fecha
   - Horas trabajadas
   - Actividad realizada
5. **"Guardar"**

### 5. Evaluación Final

Al completar 480 horas:

1. Dashboard → **"Evaluaciones Finales"**
2. Seleccionar practicante
3. Completar formulario:
   - **Desempeño Técnico** (1-5)
   - **Trabajo en Equipo** (1-5)
   - **Puntualidad** (1-5)
   - **Iniciativa** (1-5)
   - **Actitud** (1-5)
   - **Comentarios generales**
   - **Nota Final** (calculada automáticamente)
4. **"Enviar Evaluación"**

---

## 🎓 Coordinador Académico

### 1. Dashboard del Coordinador

```
┌─────────────────────────────────────────────┐
│  🎓 Panel del Coordinador                   │
├─────────────────────────────────────────────┤
│  📊 Estadísticas Generales                  │
│  • Prácticas Activas: 45                    │
│  • Estudiantes: 120                         │
│  • Empresas Validadas: 35                   │
│  • Documentos Pendientes: 12                │
│                                             │
│  ⏳ Solicitudes Pendientes (8)              │
│  • Juan Pérez - TechCorp SAC                │
│  • María López - InnovaIT SAC               │
│                                             │
│  📈 Métricas del Mes                        │
│  • Prácticas Completadas: 15                │
│  • Promedio General: 15.8/20                │
│  • Tasa de Aprobación: 94%                  │
└─────────────────────────────────────────────┘
```

### 2. Aprobar Solicitudes

1. Dashboard → **"Solicitudes Pendientes"**
2. Revisar solicitud:
   - Datos del estudiante
   - Requisitos académicos (semestre, promedio)
   - Empresa y convenio
   - Documentos adjuntos
3. Verificar:
   - ✅ Estudiante en semestre 6+
   - ✅ Promedio ≥ 12.0
   - ✅ Empresa validada
   - ✅ Documentos completos
4. Acción:
   - **"Aprobar"**: Asignar supervisor, iniciar práctica
   - **"Observar"**: Solicitar correcciones
   - **"Rechazar"**: Con justificación

### 3. Asignar Supervisores

1. Solicitud aprobada → **"Asignar Supervisor"**
2. Buscar supervisor en la empresa
3. Si no existe:
   - **"Crear Supervisor"**
   - Ingresar datos
   - Enviar invitación por email
4. Asignar y **"Confirmar"**

### 4. Generar Reportes

#### Reporte de Prácticas

1. Dashboard → **"Reportes"** → **"Prácticas"**
2. Filtros:
   - Periodo (fecha inicio/fin)
   - Estado (activas, completadas, todas)
   - Escuela profesional
   - Empresa
3. Formato:
   - Excel (.xlsx)
   - CSV (.csv)
   - PDF (próximamente)
4. **"Generar"** → **"Descargar"**

#### Reporte de Estudiantes

1. **"Reportes"** → **"Estudiantes"**
2. Filtros:
   - Escuela profesional
   - Semestre
   - Con/sin práctica
3. **"Generar"**

#### Estadísticas Avanzadas

1. **"Reportes"** → **"Estadísticas"**
2. Ver:
   - Timeline de prácticas
   - Estudiantes por carrera
   - Empresas por sector
   - Tasa de completitud
   - Promedios generales
3. Exportar en Excel/CSV

### 5. Gestión de Empresas

1. Dashboard → **"Empresas"**
2. **"Nueva Empresa"**:
   - RUC (validación automática con SUNAT)
   - Razón social
   - Sector económico
   - Contacto
   - **"Guardar"**
3. **"Validar Empresa"**:
   - Revisar datos
   - Aprobar o rechazar

---

## 📝 Secretaria

### 1. Dashboard de Secretaría

```
┌─────────────────────────────────────────────┐
│  📝 Panel de Secretaría                     │
├─────────────────────────────────────────────┤
│  ⏳ Validaciones Pendientes (15)            │
│  • Documentos: 8                            │
│  • Empresas: 4                              │
│  • Estudiantes: 3                           │
│                                             │
│  📋 Registros Recientes (24h)               │
│  • 5 nuevos estudiantes                     │
│  • 2 nuevas empresas                        │
│  • 12 documentos cargados                   │
│                                             │
│  📊 Estado de Documentos                    │
│  • Pendientes: 15                           │
│  • Aprobados Hoy: 8                         │
│  • Observados: 3                            │
└─────────────────────────────────────────────┘
```

### 2. Validar Documentos

1. Dashboard → **"Documentos Pendientes"**
2. Seleccionar documento
3. Descargar y revisar PDF
4. Verificar:
   - ✅ Formato correcto
   - ✅ Firmas y sellos
   - ✅ Información completa
   - ✅ Fecha vigente
5. Acción:
   - **"Aprobar"**: Documento válido
   - **"Observar"**: Requiere correcciones
   - **"Rechazar"**: No cumple requisitos
6. Agregar comentarios
7. **"Enviar"**

### 3. Registrar Estudiantes

1. Dashboard → **"Estudiantes"** → **"Nuevo"**
2. Ingresar datos:
   - Código de estudiante (YYYY + 6 dígitos)
   - Email institucional
   - Nombre completo
   - Escuela profesional
   - Semestre actual
   - Promedio ponderado
3. **"Crear Cuenta"**
4. Sistema envía email de bienvenida

### 4. Registrar Empresas

1. Dashboard → **"Empresas"** → **"Nueva"**
2. Ingresar:
   - RUC (11 dígitos)
   - Razón social
   - Sector económico
   - Dirección
   - Teléfono
   - Email
   - Contacto principal
3. **"Guardar"**
4. Esperar validación del coordinador

### 5. Aprobar Solicitudes Iniciales

1. Dashboard → **"Solicitudes"**
2. Revisar solicitud
3. Verificar documentación básica
4. Aprobar (pasa a coordinador) o Observar

---

## ⚙️ Administrador

### 1. Panel de Administración

Acceso: `http://sistema.upeu.edu.pe/admin/`

### 2. Gestión de Usuarios

1. Admin Panel → **"Users"**
2. Ver todos los usuarios
3. Acciones:
   - Crear/editar/eliminar usuarios
   - Cambiar roles
   - Resetear contraseñas
   - Bloquear/desbloquear cuentas

### 3. Configuración del Sistema

1. Admin Panel → **"Configuración"**
2. Ajustar:
   - Horas mínimas de práctica
   - Nota mínima de aprobación
   - Tiempo de sesión
   - Límites de carga de archivos
   - Configuración de emails

### 4. Auditoría y Logs

1. Admin Panel → **"Logs de Seguridad"**
2. Ver:
   - Inicios de sesión
   - Accesos fallidos
   - Cambios en permisos
   - Operaciones críticas

### 5. Respaldos

1. Admin Panel → **"Backups"**
2. **"Crear Backup Ahora"**
3. Programar backups automáticos
4. Restaurar desde backup

---

## 🔄 Procesos Principales

### Flujo Completo de Práctica

```
1. ESTUDIANTE
   └─> Registra solicitud
   └─> Carga documentos
   
2. SECRETARIA
   └─> Valida documentos
   └─> Aprueba solicitud inicial
   
3. COORDINADOR
   └─> Revisa requisitos académicos
   └─> Aprueba solicitud
   └─> Asigna supervisor
   
4. PRÁCTICA EN CURSO
   └─> Estudiante realiza actividades
   └─> Registra horas y tareas
   └─> Sube informes mensuales
   
5. SUPERVISOR
   └─> Evalúa informes
   └─> Registra avance
   └─> Evalúa desempeño
   
6. FINALIZACIÓN
   └─> Estudiante completa 480 horas
   └─> Sube informe final
   └─> Coordinador aprueba
   └─> Sistema genera certificado
   
7. CERTIFICADO
   └─> Estudiante descarga
   └─> Archivo en historial
```

---

## ❓ Preguntas Frecuentes

### Para Estudiantes

**Q: ¿Cuántas horas debo completar?**  
A: Mínimo 480 horas de práctica efectiva.

**Q: ¿Puedo cambiar de empresa durante la práctica?**  
A: Sí, pero debes iniciar un nuevo proceso. Las horas previas pueden no ser convalidables.

**Q: ¿Qué pasa si repruebo un informe?**  
A: Debes corregir y volver a enviar. Tienes 3 intentos máximo.

**Q: ¿Cuándo puedo descargar mi certificado?**  
A: Después de completar todas las horas y que el coordinador apruebe el informe final.

### Para Supervisores

**Q: ¿Cómo evalúo a un practicante?**  
A: Desde tu dashboard, sección "Informes Pendientes".

**Q: ¿Puedo tener varios practicantes?**  
A: Sí, sin límite. Todos aparecerán en tu dashboard.

**Q: ¿Cómo registro horas?**  
A: Dashboard → Practicantes → Seleccionar → "Registrar Horas".

### Para Coordinadores

**Q: ¿Cómo asigno un supervisor?**  
A: Al aprobar una solicitud, sistema te pide asignar supervisor.

**Q: ¿Puedo reasignar un supervisor?**  
A: Sí, desde la práctica → "Cambiar Supervisor".

**Q: ¿Cómo genero reportes masivos?**  
A: Dashboard → Reportes → Seleccionar tipo y filtros → Exportar.

---

## 📞 Soporte Técnico

### Contacto

- **Email**: soporte.practicas@upeu.edu.pe
- **Teléfono**: (01) 618-8888 Anexo 2345
- **Horario**: Lunes a Viernes, 8:00 AM - 5:00 PM

### Problemas Comunes

**No puedo iniciar sesión**:
- Verifica tu email y contraseña
- Usa "¿Olvidaste tu contraseña?"
- Contacta a soporte si persiste

**No puedo cargar documentos**:
- Verifica que el archivo sea PDF
- Tamaño máximo: 5MB
- Intenta con otro navegador

**No recibo notificaciones**:
- Revisa carpeta de spam
- Verifica tu email en el perfil
- Actualiza tus preferencias

---

## 📚 Recursos Adicionales

- 📖 [Guía de Instalación](GUIA_INSTALACION.md)
- 💻 [Guía de Desarrollo](GUIA_DESARROLLO.md)
- 🚀 [Guía de Deployment](DEPLOYMENT_GUIDE.md)
- 📊 [Documentación API](README_DASHBOARDS.md)

---

**Universidad Peruana Unión**  
**Sistema de Gestión de Prácticas Profesionales**  
**Versión 2.0** - Octubre 2024
