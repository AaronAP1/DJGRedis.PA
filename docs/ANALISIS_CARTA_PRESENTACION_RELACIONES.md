# 📊 Análisis: Relaciones en Carta de Presentación

## 🎯 Problema Identificado

Actualmente, el modelo `PresentationLetterRequest` utiliza **campos de texto libre** para información que debería estar **relacionada mediante ForeignKeys** a tablas existentes.

---

## 🔍 Análisis de Campos Actuales

### 1️⃣ Escuela Profesional (E.P.)

**Estado Actual:**
```python
ep = models.CharField(
    'E.P. (Escuela Profesional)',
    max_length=200,
    help_text='Ejemplo: Ingeniería de Sistemas'
)
```

**Problema:**
- ❌ Es texto libre (puede tener errores de tipeo)
- ❌ No valida que la escuela exista
- ❌ No permite relaciones con la tabla `upeu_escuela`
- ❌ Duplica información que ya existe en `StudentProfile.escuela`

**Solución Propuesta:**
```python
escuela = models.ForeignKey(
    'School',
    on_delete=models.PROTECT,
    related_name='presentation_letters',
    verbose_name='Escuela Profesional',
    help_text='Escuela profesional del estudiante',
    null=True,  # Temporal para migración
    blank=True
)
```

**Ventajas:**
- ✅ Valida que la escuela exista en la BD
- ✅ Permite consultas relacionadas
- ✅ Auto-completa desde `StudentProfile.escuela`
- ✅ Mantiene integridad referencial

---

### 2️⃣ Datos de la Empresa

**Estado Actual:**
```python
company_name = models.CharField('Nombre de la Empresa', max_length=255)
company_representative = models.CharField('Nombre del Representante', max_length=200)
company_position = models.CharField('Cargo del Representante', max_length=100)
company_phone = models.CharField('Teléfono - Fax', max_length=50)
company_address = models.TextField('Dirección de la Empresa')
```

**Problema:**
- ❌ Los datos de empresa no se guardan en `upeu_empresa`
- ❌ No permite reutilizar empresas existentes
- ❌ Duplica información si varios estudiantes van a la misma empresa
- ❌ No valida RUC de empresa
- ❌ Dificulta reportes de empresas que reciben practicantes

**Solución Propuesta:**

#### Opción A: Relacionar con Empresa Existente (Recomendada)
```python
empresa = models.ForeignKey(
    'Company',
    on_delete=models.PROTECT,
    related_name='presentation_letters',
    verbose_name='Empresa',
    help_text='Empresa donde realizará la práctica',
    null=True,  # Temporal para migración
    blank=True
)

# Campos adicionales específicos de la carta
company_representative = models.CharField(
    'Nombre del Representante',
    max_length=200,
    help_text='Persona de contacto para esta solicitud específica'
)

company_position = models.CharField(
    'Cargo del Representante / Grado Académico',
    max_length=100,
    help_text='Ejemplo: Gerente de Recursos Humanos'
)
```

#### Opción B: Permitir Crear Empresa en el Proceso
```python
# Permitir seleccionar empresa existente O crear nueva
empresa = models.ForeignKey(
    'Company',
    on_delete=models.PROTECT,
    related_name='presentation_letters',
    verbose_name='Empresa',
    null=True,
    blank=True
)

# Si no selecciona empresa existente, guardar datos temporales
# Estos datos se usan para crear la empresa después
temp_company_data = models.JSONField(
    'Datos Temporales de Empresa',
    null=True,
    blank=True,
    help_text='Datos de empresa pendiente de validación'
)
```

---

## 📋 Propuesta de Modelo Actualizado

### Modelo `PresentationLetterRequest` Mejorado

```python
class PresentationLetterRequest(models.Model):
    """
    Solicitud de Carta de Presentación.
    """
    
    # ========================================================================
    # RELACIONES PRINCIPALES
    # ========================================================================
    
    student = models.ForeignKey(
        'StudentProfile',
        on_delete=models.CASCADE,
        related_name='presentation_letter_requests',
        verbose_name='Estudiante'
    )
    
    # NUEVO: Relación con Escuela
    escuela = models.ForeignKey(
        'School',
        on_delete=models.PROTECT,
        related_name='presentation_letters',
        verbose_name='Escuela Profesional',
        null=True,
        blank=True
    )
    
    # NUEVO: Relación con Empresa
    empresa = models.ForeignKey(
        'Company',
        on_delete=models.PROTECT,
        related_name='presentation_letters',
        verbose_name='Empresa',
        null=True,
        blank=True
    )
    
    assigned_secretary = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_letter_requests'
    )
    
    # ========================================================================
    # DATOS DEL ESTUDIANTE (desnormalizados para el PDF)
    # ========================================================================
    
    # MANTENER para compatibilidad y para el PDF
    ep = models.CharField(
        'E.P. (Texto)',
        max_length=200,
        help_text='Auto-rellenado desde escuela.nombre',
        blank=True
    )
    
    student_full_name = models.CharField('Nombre Completo', max_length=200)
    student_code = models.CharField('Código', max_length=20)
    student_email = models.EmailField('Email', max_length=100)
    
    year_of_study = models.CharField('Año de Estudios', max_length=50)
    study_cycle = models.CharField('Ciclo de Estudios', max_length=10)
    
    # ========================================================================
    # DATOS DE LA EMPRESA (desnormalizados para el PDF)
    # ========================================================================
    
    # MANTENER para el PDF (auto-rellenados desde empresa)
    company_name = models.CharField(
        'Nombre de la Empresa (Texto)',
        max_length=255,
        help_text='Auto-rellenado desde empresa.nombre',
        blank=True
    )
    
    company_address = models.TextField(
        'Dirección (Texto)',
        help_text='Auto-rellenado desde empresa.direccion',
        blank=True
    )
    
    # Datos específicos de la carta (NO están en Company)
    company_representative = models.CharField(
        'Nombre del Representante',
        max_length=200,
        help_text='Persona de contacto específica para esta solicitud'
    )
    
    company_position = models.CharField(
        'Cargo del Representante',
        max_length=100
    )
    
    company_phone = models.CharField(
        'Teléfono de Contacto',
        max_length=50,
        help_text='Puede ser diferente al teléfono principal de la empresa'
    )
    
    practice_area = models.CharField(
        'Área de Práctica',
        max_length=100
    )
    
    start_date = models.DateField('Fecha de Inicio')
    
    # ... resto de campos (status, timestamps, etc.)
```

---

## 🔄 Cambios en Serializers

### Serializer de Creación

```python
class PresentationLetterRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear/actualizar solicitud.
    """
    
    # Campos de solo lectura (auto-rellenados)
    student_full_name = serializers.CharField(read_only=True)
    student_code = serializers.CharField(read_only=True)
    student_email = serializers.CharField(read_only=True)
    ep = serializers.CharField(read_only=True)
    company_name = serializers.CharField(read_only=True)
    company_address = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    
    # NUEVOS: IDs para relaciones
    escuela_id = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(estado='ACTIVO'),
        source='escuela',
        required=False,
        allow_null=True,
        help_text='ID de la escuela profesional'
    )
    
    empresa_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.filter(estado='ACTIVO'),
        source='empresa',
        required=False,
        allow_null=True,
        help_text='ID de la empresa (si ya existe)'
    )
    
    class Meta:
        model = PresentationLetterRequest
        fields = [
            'id',
            # Relaciones (IDs)
            'escuela_id',
            'empresa_id',
            # Datos del estudiante (auto-rellenados)
            'ep',
            'student_full_name',
            'student_code',
            'student_email',
            # Datos ingresados
            'year_of_study',
            'study_cycle',
            # Datos de la empresa (algunos auto-rellenados)
            'company_name',  # Auto-rellenado si hay empresa_id
            'company_address',  # Auto-rellenado si hay empresa_id
            'company_representative',  # Ingresado manualmente
            'company_position',  # Ingresado manualmente
            'company_phone',  # Ingresado manualmente
            'practice_area',
            'start_date',
            # Metadatos
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'ep',
            'student_full_name',
            'student_code',
            'student_email',
            'company_name',
            'company_address',
            'status',
            'created_at',
            'updated_at',
        ]
```

### Serializer de Detalle

```python
class PresentationLetterRequestDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado con información expandida.
    """
    
    student_info = serializers.SerializerMethodField()
    escuela_info = serializers.SerializerMethodField()
    empresa_info = serializers.SerializerMethodField()
    secretary_info = serializers.SerializerMethodField()
    
    def get_escuela_info(self, obj):
        """Información de la escuela."""
        if obj.escuela:
            return {
                'id': obj.escuela.id,
                'nombre': obj.escuela.nombre,
                'codigo': obj.escuela.codigo,
            }
        return None
    
    def get_empresa_info(self, obj):
        """Información de la empresa."""
        if obj.empresa:
            return {
                'id': obj.empresa.id,
                'nombre': obj.empresa.nombre,
                'ruc': obj.empresa.ruc,
                'direccion': obj.empresa.direccion,
                'telefono': obj.empresa.telefono,
                'correo': obj.empresa.correo,
            }
        return None
```

---

## 📝 Cambios en el Modelo al Guardar

```python
def save(self, *args, **kwargs):
    """Auto-rellenar datos desnormalizados."""
    
    # Auto-rellenar datos del estudiante
    if not self.pk and self.student_id:
        self.student_full_name = f"{self.student.usuario.nombres} {self.student.usuario.apellidos}"
        self.student_code = self.student.codigo
        self.student_email = self.student.usuario.correo
        
        # Auto-asignar escuela desde el perfil del estudiante
        if self.student.escuela:
            self.escuela = self.student.escuela
            self.ep = self.student.escuela.nombre
    
    # Auto-rellenar datos de la empresa si se seleccionó una
    if self.empresa:
        self.company_name = self.empresa.nombre
        self.company_address = self.empresa.direccion or ''
    
    super().save(*args, **kwargs)
```

---

## 🎨 Cambios en el Frontend

### Formulario de Solicitud

```javascript
// En lugar de campo de texto libre para E.P.
<select name="escuela_id">
  <option value="">Seleccionar E.P.</option>
  {escuelas.map(e => (
    <option key={e.id} value={e.id}>{e.nombre}</option>
  ))}
</select>

// Para empresa: combo con búsqueda + opción "Otra empresa"
<select name="empresa_id">
  <option value="">Nueva empresa (llenar datos)</option>
  {empresas.map(emp => (
    <option key={emp.id} value={emp.id}>
      {emp.nombre} - RUC: {emp.ruc}
    </option>
  ))}
</select>

// Si selecciona empresa existente, auto-completar:
// - company_name (readonly)
// - company_address (readonly)
// - company_phone (puede editar si es teléfono específico)

// Si no selecciona empresa, pedir todos los datos:
// - company_name (input)
// - company_address (textarea)
// - company_phone (input)
// ... y crear la empresa en el proceso de aprobación
```

---

## 🚀 Plan de Migración

### Paso 1: Agregar Nuevos Campos (Nullable)
```python
# Migration 0017_add_relations_to_presentation_letter.py
operations = [
    migrations.AddField(
        model_name='presentationletterrequest',
        name='escuela',
        field=models.ForeignKey(
            blank=True,
            null=True,
            on_delete=django.db.models.deletion.PROTECT,
            related_name='presentation_letters',
            to='database.school',
            verbose_name='Escuela Profesional'
        ),
    ),
    migrations.AddField(
        model_name='presentationletterrequest',
        name='empresa',
        field=models.ForeignKey(
            blank=True,
            null=True,
            on_delete=django.db.models.deletion.PROTECT,
            related_name='presentation_letters',
            to='database.company',
            verbose_name='Empresa'
        ),
    ),
]
```

### Paso 2: Migrar Datos Existentes
```python
# Script de migración de datos
def migrate_existing_data():
    """Migrar registros existentes."""
    from src.adapters.secondary.database.models import (
        PresentationLetterRequest, School, Company
    )
    
    for letter in PresentationLetterRequest.objects.all():
        # Migrar escuela desde el perfil del estudiante
        if letter.student and letter.student.escuela:
            letter.escuela = letter.student.escuela
        
        # Intentar encontrar empresa por nombre
        if letter.company_name:
            empresa = Company.objects.filter(
                nombre__iexact=letter.company_name.strip()
            ).first()
            
            if empresa:
                letter.empresa = empresa
        
        letter.save()
```

### Paso 3: Validar y Hacer NOT NULL (Opcional)
```python
# Después de migración, hacer campos obligatorios
# Solo si queremos forzar que siempre tengan relación
```

---

## 📊 Estructura de Request/Response API

### POST /api/v2/presentation-letters/

**Request Body:**
```json
{
  "escuela_id": 1,
  "empresa_id": 5,
  "year_of_study": "Quinto año",
  "study_cycle": "IX",
  "company_representative": "Juan Pérez García",
  "company_position": "Gerente de RRHH",
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
  "company_position": "Gerente de RRHH",
  "company_phone": "01-2345678",
  "practice_area": "Desarrollo de Software",
  "start_date": "2025-03-01",
  "status": "DRAFT",
  "created_at": "2025-11-02T10:00:00Z"
}
```

### GET /api/v2/presentation-letters/{id}/

**Response (Detallado):**
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
  "escuela_info": {
    "id": 1,
    "nombre": "Ingeniería de Sistemas",
    "codigo": "EP-IS"
  },
  "empresa_info": {
    "id": 5,
    "nombre": "Tech Solutions SAC",
    "ruc": "20123456789",
    "direccion": "Av. Ejemplo 123, Lima",
    "telefono": "01-9876543",
    "correo": "contacto@techsolutions.com"
  },
  "ep": "Ingeniería de Sistemas",
  "student_full_name": "María García López",
  "student_code": "2020123456",
  "company_name": "Tech Solutions SAC",
  "company_representative": "Juan Pérez García",
  "company_position": "Gerente de RRHH",
  "company_phone": "01-2345678",
  "practice_area": "Desarrollo de Software",
  "start_date": "2025-03-01",
  "status": "APPROVED",
  "created_at": "2025-11-02T10:00:00Z",
  "updated_at": "2025-11-02T15:30:00Z"
}
```

---

## 🎯 Endpoints Auxiliares Necesarios

### 1. Listar Escuelas Activas
```
GET /api/v2/schools/?status=ACTIVO
```

### 2. Listar Empresas Activas
```
GET /api/v2/companies/?status=ACTIVO&search=tech
```

### 3. Crear Empresa desde Carta de Presentación
```
POST /api/v2/companies/
{
  "nombre": "Nueva Empresa SAC",
  "ruc": "20987654321",
  "razon_social": "Nueva Empresa Sociedad Anónima Cerrada",
  "direccion": "Av. Nueva 456",
  "telefono": "01-5551234",
  "correo": "info@nuevaempresa.com",
  "sector_economico": "Tecnología"
}
```

---

## ✅ Beneficios de los Cambios

### Integridad de Datos
- ✅ Valida que escuelas y empresas existan
- ✅ Evita errores de tipeo
- ✅ Mantiene referencias consistentes

### Reutilización
- ✅ Empresas pueden recibir múltiples practicantes
- ✅ Datos de empresa centralizados
- ✅ Actualización automática si cambian datos de empresa

### Reportes y Análisis
- ✅ Consultar cuántas cartas por escuela
- ✅ Top empresas que reciben practicantes
- ✅ Filtrar por empresa, escuela, etc.

### Compatibilidad
- ✅ Mantiene campos de texto para el PDF
- ✅ Migración gradual sin romper código existente
- ✅ Auto-rellenado inteligente

---

## 🔧 Implementación Recomendada

**Enfoque Híbrido (Recomendado):**

1. **Escuela**: SIEMPRE ForeignKey (auto-asignada desde StudentProfile)
2. **Empresa**: 
   - Permitir seleccionar empresa existente (ForeignKey)
   - O ingresar datos manualmente (campos de texto)
   - En aprobación, secretaria crea la empresa en `upeu_empresa`

Este enfoque es más flexible y user-friendly.

---

## 📌 Resumen

| Campo | Actual | Propuesto | Motivo |
|-------|--------|-----------|--------|
| `ep` | CharField | ForeignKey a `School` + CharField | Relación + texto para PDF |
| `company_*` | CharField | ForeignKey a `Company` + CharField | Relación opcional + texto para PDF |
| Auto-rellenado | Manual | Automático desde relaciones | Menos errores |
| Validación | Básica | Con integridad referencial | Más robusto |

---

**Fecha:** 2025-11-02  
**Estado:** Propuesta para implementación  
**Prioridad:** Alta (mejora significativa de integridad de datos)
