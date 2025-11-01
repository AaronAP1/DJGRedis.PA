# 📋 Nuevo Flujo: Solicitud de Carta de Presentación

## 🎯 Problema Identificado

El flujo actual del backend **NO coincide** con el proceso real de la Universidad Peruana Unión.

### ❌ Flujo Actual (Incorrecto)
1. Estudiante crea práctica completa con todos los datos
2. Secretaria valida documentos
3. Coordinador aprueba

### ✅ Flujo Real (según proceso institucional)
1. **Estudiante solicita Carta de Presentación** (solo datos básicos)
2. **Secretaria valida y genera Carta de Presentación**
3. **Estudiante va a empresa** con carta física/digital
4. **Empresa firma Convenio** de aceptación
5. **Estudiante crea Práctica completa** (ahora sí con todos los datos)
6. **Coordinador/Supervisor revisan y aprueban**

---

## 🏗️ Arquitectura Propuesta

### Nuevo Modelo: `PresentationLetterRequest`

```python
# src/domain/entities/presentation_letter_request.py

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from typing import Optional

@dataclass
class PresentationLetterRequest:
    """
    Solicitud de Carta de Presentación.
    
    Primer paso del proceso de prácticas. El estudiante solicita
    una carta de presentación de la universidad para presentar
    ante una empresa.
    """
    id: UUID
    
    # Datos del Estudiante (auto-rellenados del token)
    student_id: UUID
    student_name: str
    student_code: str
    student_email: str
    year_of_study: str  # "Año de estudios" - Ej: "Quinto año"
    study_cycle: str    # "Ciclo de estudios" - Ej: "IX"
    
    # Datos de la Empresa (ingresados manualmente)
    company_name: str           # Nombre de la empresa
    company_representative: str  # Nombre del representante
    company_position: str       # Cargo del representante (Grado académico)
    company_phone: str          # Teléfono - Fax
    company_address: str        # Dirección
    practice_area: str          # Área de Práctica
    
    # Asignación de Secretaria
    assigned_secretary_id: Optional[UUID] = None
    
    # Metadatos
    status: str  # DRAFT, PENDING, APPROVED, REJECTED, GENERATED
    start_date: datetime  # Fecha Inicio
    created_at: datetime
    updated_at: datetime
    
    # Resultado
    letter_document_id: Optional[UUID] = None  # ID del documento generado
    rejection_reason: Optional[str] = None
    
    def __post_init__(self):
        """Validaciones básicas."""
        if not self.student_name or not self.student_code:
            raise ValueError("Datos del estudiante requeridos")
        if not self.company_name:
            raise ValueError("Nombre de empresa requerido")
```

---

## 📊 Estados del Nuevo Flujo

### Estados de `PresentationLetterRequest`

```
DRAFT          → Borrador (estudiante editando)
    ↓
PENDING        → Enviado a secretaría
    ↓
APPROVED       → Secretaria aprueba
    ↓
GENERATED      → Carta de presentación generada (PDF)
    ↓
USED           → Estudiante la usó para crear práctica

Estados alternativos:
REJECTED       → Secretaria rechaza (estudiante debe corregir)
```

### Diagrama de Flujo Completo

```
┌─────────────────────────────────────────────────────────────────┐
│ PASO 1: Solicitud de Carta de Presentación                     │
└─────────────────────────────────────────────────────────────────┘
         │
         │ Estudiante crea PresentationLetterRequest
         │ - E.P., Alumno, Código
         │ - Año de estudios, Ciclo
         │ - Empresa, Representante
         │ - Área de Práctica
         │ - Fecha Inicio
         ↓
    [DRAFT] ──submit()──> [PENDING]
         │
         │
┌─────────────────────────────────────────────────────────────────┐
│ PASO 2: Validación de Secretaría                               │
└─────────────────────────────────────────────────────────────────┘
         │
         │ Secretaria valida:
         │ ✅ Datos correctos
         │ ✅ Estudiante elegible
         │ ✅ Empresa válida
         ↓
    [PENDING] ──approve()──> [APPROVED] ──generate()──> [GENERATED]
         │                                                    │
         │ reject()                            Sistema genera PDF
         ↓                                                    │
    [REJECTED]                           letter_document_id (UUID)
         │
         │
┌─────────────────────────────────────────────────────────────────┐
│ PASO 3: Estudiante recibe carta                                │
└─────────────────────────────────────────────────────────────────┘
         │
         │ Descarga PDF de carta de presentación
         │ Va a la empresa físicamente
         │
         │
┌─────────────────────────────────────────────────────────────────┐
│ PASO 4: Firma de Convenio en Empresa                           │
└─────────────────────────────────────────────────────────────────┘
         │
         │ Empresa firma convenio
         │ Estudiante escanea documento
         │
         │
┌─────────────────────────────────────────────────────────────────┐
│ PASO 5: Creación de Práctica Completa                          │
└─────────────────────────────────────────────────────────────────┘
         │
         │ Estudiante crea Practice
         │ - Referencia a PresentationLetterRequest
         │ - Supervisor asignado
         │ - Convenio firmado (upload)
         │ - Carta de aceptación
         │ - Plan de trabajo
         ↓
    Practice [DRAFT] ──submit()──> [PENDING]
         │
         │
┌─────────────────────────────────────────────────────────────────┐
│ PASO 6: Aprobación de Coordinador/Supervisor                   │
└─────────────────────────────────────────────────────────────────┘
         │
         │ Coordinador revisa y aprueba
         ↓
    Practice [PENDING] ──approve()──> [APPROVED]
         │
         │ Estudiante inicia
         ↓
    Practice [APPROVED] ──start()──> [IN_PROGRESS]
```

---

## 🔧 Cambios en el Backend

### 1. Nuevos Archivos a Crear

```
src/
├── domain/
│   ├── entities/
│   │   └── presentation_letter_request.py  ✨ NUEVO
│   └── enums.py  (agregar PresentationLetterStatus)
│
├── ports/
│   ├── primary/
│   │   └── api_ports.py  (agregar PresentationLetterPort)
│   └── secondary/
│       └── repository_ports.py  (agregar PresentationLetterRepositoryPort)
│
├── adapters/
│   ├── primary/
│   │   └── rest_api/
│   │       ├── viewsets/
│   │       │   └── presentation_letter_viewset.py  ✨ NUEVO
│   │       └── serializers/
│   │           └── presentation_letter_serializer.py  ✨ NUEVO
│   │
│   └── secondary/
│       └── persistence/
│           └── presentation_letter_repository.py  ✨ NUEVO
│
└── application/
    └── use_cases/
        ├── create_presentation_letter_request.py  ✨ NUEVO
        ├── submit_presentation_letter_request.py  ✨ NUEVO
        ├── approve_presentation_letter_request.py  ✨ NUEVO
        └── generate_presentation_letter_pdf.py  ✨ NUEVO
```

---

### 2. Modelo Django

```python
# src/adapters/secondary/persistence/models/presentation_letter_request.py

from django.db import models
from django.core.validators import MinLengthValidator
import uuid

class PresentationLetterRequestModel(models.Model):
    """
    Modelo de Solicitud de Carta de Presentación.
    
    Primer paso del proceso de prácticas profesionales.
    """
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Borrador'
        PENDING = 'PENDING', 'Pendiente'
        APPROVED = 'APPROVED', 'Aprobado'
        REJECTED = 'REJECTED', 'Rechazado'
        GENERATED = 'GENERATED', 'Carta Generada'
        USED = 'USED', 'Usada en Práctica'
    
    # Primary Key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relaciones
    student = models.ForeignKey(
        'Student',
        on_delete=models.CASCADE,
        related_name='presentation_letter_requests',
        verbose_name='Estudiante'
    )
    
    assigned_secretary = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'SECRETARIA'},
        related_name='assigned_letter_requests',
        verbose_name='Secretaria Asignada'
    )
    
    # Datos del Estudiante (desnormalizados para carta)
    student_name = models.CharField(max_length=200, verbose_name='Nombre Completo')
    student_code = models.CharField(max_length=20, verbose_name='Código Estudiante')
    student_email = models.EmailField(verbose_name='Email Estudiante')
    year_of_study = models.CharField(max_length=50, verbose_name='Año de Estudios')
    study_cycle = models.CharField(max_length=10, verbose_name='Ciclo de Estudios')
    
    # Datos de la Empresa
    company_name = models.CharField(max_length=255, verbose_name='Nombre de la Empresa')
    company_representative = models.CharField(max_length=200, verbose_name='Nombre del Representante')
    company_position = models.CharField(max_length=100, verbose_name='Cargo del Representante')
    company_phone = models.CharField(max_length=50, verbose_name='Teléfono - Fax')
    company_address = models.TextField(verbose_name='Dirección de la Empresa')
    practice_area = models.CharField(max_length=100, verbose_name='Área de Práctica')
    
    # Fechas
    start_date = models.DateField(verbose_name='Fecha de Inicio')
    
    # Estado
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='Estado'
    )
    
    # Resultado
    letter_document = models.ForeignKey(
        'Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presentation_letter',
        verbose_name='Documento de Carta'
    )
    
    rejection_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name='Motivo de Rechazo'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')
    
    class Meta:
        db_table = 'presentation_letter_requests'
        verbose_name = 'Solicitud de Carta de Presentación'
        verbose_name_plural = 'Solicitudes de Carta de Presentación'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['assigned_secretary', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Carta {self.student_code} - {self.company_name} ({self.status})"
    
    def can_edit(self):
        """Permite edición solo en estado DRAFT o REJECTED."""
        return self.status in [self.Status.DRAFT, self.Status.REJECTED]
    
    def can_submit(self):
        """Permite envío solo desde DRAFT."""
        return self.status == self.Status.DRAFT
    
    def can_approve(self):
        """Permite aprobación solo desde PENDING."""
        return self.status == self.Status.PENDING
```

---

### 3. Serializers

```python
# src/adapters/primary/rest_api/serializers/presentation_letter_serializer.py

from rest_framework import serializers
from src.adapters.secondary.persistence.models import PresentationLetterRequestModel

class PresentationLetterRequestSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar solicitud de carta de presentación."""
    
    # Campos de solo lectura (auto-rellenados)
    student_name = serializers.CharField(read_only=True)
    student_code = serializers.CharField(read_only=True)
    student_email = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    
    class Meta:
        model = PresentationLetterRequestModel
        fields = [
            'id',
            # Datos del estudiante (auto-rellenados)
            'student',
            'student_name',
            'student_code',
            'student_email',
            'year_of_study',
            'study_cycle',
            # Datos de la empresa (ingresados por estudiante)
            'company_name',
            'company_representative',
            'company_position',
            'company_phone',
            'company_address',
            'practice_area',
            'start_date',
            # Metadatos
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'student', 'status', 'created_at', 'updated_at']
    
    def validate_year_of_study(self, value):
        """Validar año de estudios."""
        valid_years = ['Tercer año', 'Cuarto año', 'Quinto año', 'Sexto año']
        if value not in valid_years:
            raise serializers.ValidationError(
                f"Año de estudios debe ser uno de: {', '.join(valid_years)}"
            )
        return value
    
    def validate_study_cycle(self, value):
        """Validar ciclo de estudios."""
        import re
        if not re.match(r'^[IVX]+$', value):
            raise serializers.ValidationError("Ciclo debe estar en números romanos (ej: IX, X)")
        return value


class PresentationLetterRequestDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado incluyendo documentos y secretaria."""
    
    from src.adapters.primary.rest_api.serializers import StudentSerializer, UserSerializer
    
    student = StudentSerializer(read_only=True)
    assigned_secretary = UserSerializer(read_only=True)
    
    class Meta:
        model = PresentationLetterRequestModel
        fields = '__all__'


class SubmitPresentationLetterSerializer(serializers.Serializer):
    """Serializer para enviar solicitud a secretaría."""
    pass  # No requiere datos adicionales


class ApprovePresentationLetterSerializer(serializers.Serializer):
    """Serializer para aprobar solicitud (Secretaria)."""
    pass


class RejectPresentationLetterSerializer(serializers.Serializer):
    """Serializer para rechazar solicitud."""
    rejection_reason = serializers.CharField(
        required=True,
        max_length=500,
        help_text="Motivo del rechazo"
    )


class GeneratePresentationLetterSerializer(serializers.Serializer):
    """Serializer para generar PDF de carta."""
    pass
```

---

### 4. ViewSet

```python
# src/adapters/primary/rest_api/viewsets/presentation_letter_viewset.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from src.adapters.secondary.persistence.models import (
    PresentationLetterRequestModel,
    Student
)
from src.adapters.primary.rest_api.serializers import (
    PresentationLetterRequestSerializer,
    PresentationLetterRequestDetailSerializer,
    SubmitPresentationLetterSerializer,
    ApprovePresentationLetterSerializer,
    RejectPresentationLetterSerializer,
)
from src.adapters.primary.rest_api.permissions import (
    IsSecretaria,
    IsPracticante
)


class PresentationLetterRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Solicitudes de Carta de Presentación.
    
    Flujo:
    1. PRACTICANTE crea solicitud (DRAFT)
    2. PRACTICANTE envía a revisión (submit → PENDING)
    3. SECRETARIA aprueba (approve → APPROVED)
    4. SECRETARIA genera PDF (generate → GENERATED)
    5. PRACTICANTE descarga carta
    """
    
    queryset = PresentationLetterRequestModel.objects.select_related(
        'student',
        'assigned_secretary',
        'letter_document'
    )
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'list':
            return PresentationLetterRequestDetailSerializer
        return PresentationLetterRequestSerializer
    
    def get_queryset(self):
        """Filtrar según rol."""
        user = self.request.user
        
        if user.role == 'PRACTICANTE':
            # Solo sus solicitudes
            return self.queryset.filter(student__user=user)
        
        elif user.role == 'SECRETARIA':
            # Solo las asignadas o pendientes sin asignar
            return self.queryset.filter(
                models.Q(assigned_secretary=user) |
                models.Q(assigned_secretary__isnull=True, status='PENDING')
            )
        
        else:
            # Coordinadores y admins ven todas
            return self.queryset
    
    def perform_create(self, serializer):
        """Auto-rellenar datos del estudiante autenticado."""
        user = self.request.user
        
        # Obtener estudiante del usuario
        student = get_object_or_404(Student, user=user)
        
        # Guardar con datos auto-rellenados
        serializer.save(
            student=student,
            student_name=f"{student.first_name} {student.last_name}",
            student_code=student.codigo_estudiante,
            student_email=student.email,
            status='DRAFT'
        )
    
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated, IsPracticante],
        url_path='submit'
    )
    def submit(self, request, pk=None):
        """
        Enviar solicitud a secretaría.
        
        POST /api/v2/presentation-letters/{id}/submit/
        
        Transición: DRAFT → PENDING
        """
        letter_request = self.get_object()
        
        # Validar estado
        if not letter_request.can_submit():
            return Response(
                {'error': 'Solo se pueden enviar solicitudes en estado DRAFT'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cambiar estado
        letter_request.status = 'PENDING'
        letter_request.save()
        
        # TODO: Enviar notificación a secretarías
        
        serializer = self.get_serializer(letter_request)
        return Response(serializer.data)
    
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated, IsSecretaria],
        url_path='approve'
    )
    def approve(self, request, pk=None):
        """
        Aprobar solicitud (Secretaria).
        
        POST /api/v2/presentation-letters/{id}/approve/
        
        Transición: PENDING → APPROVED
        """
        letter_request = self.get_object()
        
        # Validar estado
        if not letter_request.can_approve():
            return Response(
                {'error': 'Solo se pueden aprobar solicitudes en estado PENDING'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Asignar secretaria y aprobar
        letter_request.assigned_secretary = request.user
        letter_request.status = 'APPROVED'
        letter_request.save()
        
        # TODO: Notificar al estudiante
        
        serializer = self.get_serializer(letter_request)
        return Response(serializer.data)
    
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated, IsSecretaria],
        url_path='reject'
    )
    def reject(self, request, pk=None):
        """
        Rechazar solicitud con motivo.
        
        POST /api/v2/presentation-letters/{id}/reject/
        {
            "rejection_reason": "Datos de empresa incorrectos"
        }
        
        Transición: PENDING → REJECTED
        """
        letter_request = self.get_object()
        serializer = RejectPresentationLetterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Rechazar
        letter_request.status = 'REJECTED'
        letter_request.rejection_reason = serializer.validated_data['rejection_reason']
        letter_request.assigned_secretary = request.user
        letter_request.save()
        
        # TODO: Notificar al estudiante
        
        return Response(self.get_serializer(letter_request).data)
    
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated, IsSecretaria],
        url_path='generate-pdf'
    )
    def generate_pdf(self, request, pk=None):
        """
        Generar PDF de carta de presentación.
        
        POST /api/v2/presentation-letters/{id}/generate-pdf/
        
        Transición: APPROVED → GENERATED
        """
        letter_request = self.get_object()
        
        # Validar estado
        if letter_request.status != 'APPROVED':
            return Response(
                {'error': 'Solo se pueden generar cartas aprobadas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Generar PDF usando plantilla
        # from src.application.services import PresentationLetterPDFService
        # pdf_file = PresentationLetterPDFService.generate(letter_request)
        
        # TODO: Crear Document
        # document = Document.objects.create(...)
        # letter_request.letter_document = document
        
        letter_request.status = 'GENERATED'
        letter_request.save()
        
        return Response({
            'success': True,
            'message': 'Carta de presentación generada exitosamente',
            'document_id': str(letter_request.letter_document_id) if letter_request.letter_document_id else None
        })
    
    @action(
        detail=True,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download'
    )
    def download(self, request, pk=None):
        """
        Descargar PDF de carta de presentación.
        
        GET /api/v2/presentation-letters/{id}/download/
        """
        letter_request = self.get_object()
        
        if not letter_request.letter_document:
            return Response(
                {'error': 'Carta aún no generada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # TODO: Retornar archivo PDF
        # return FileResponse(...)
        
        return Response({
            'download_url': f'/media/{letter_request.letter_document.archivo.name}'
        })
```

---

### 5. URLs

```python
# src/adapters/primary/rest_api/urls_api_v2.py

from src.adapters.primary.rest_api.viewsets import PresentationLetterRequestViewSet

# Agregar al router
router.register(
    r'presentation-letters',
    PresentationLetterRequestViewSet,
    basename='presentation-letter'
)
```

---

## 📝 Endpoints Resultantes

```
GET    /api/v2/presentation-letters/              - Listar solicitudes
POST   /api/v2/presentation-letters/              - Crear solicitud (PRACTICANTE)
GET    /api/v2/presentation-letters/{id}/         - Ver detalle
PUT    /api/v2/presentation-letters/{id}/         - Actualizar (solo DRAFT)
DELETE /api/v2/presentation-letters/{id}/         - Eliminar (solo DRAFT)

POST   /api/v2/presentation-letters/{id}/submit/      - Enviar a secretaría
POST   /api/v2/presentation-letters/{id}/approve/     - Aprobar (SECRETARIA)
POST   /api/v2/presentation-letters/{id}/reject/      - Rechazar (SECRETARIA)
POST   /api/v2/presentation-letters/{id}/generate-pdf/ - Generar PDF
GET    /api/v2/presentation-letters/{id}/download/    - Descargar PDF
```

---

## 🔄 Modificación del Modelo Practice

Ahora `Practice` debe referenciar a `PresentationLetterRequest`:

```python
# src/adapters/secondary/persistence/models/practice.py

class Practice(models.Model):
    # ... campos existentes ...
    
    # NUEVO: Referencia a solicitud de carta
    presentation_letter_request = models.ForeignKey(
        'PresentationLetterRequestModel',
        on_delete=models.PROTECT,
        related_name='practices',
        verbose_name='Solicitud de Carta de Presentación',
        help_text='Carta de presentación asociada a esta práctica'
    )
```

---

## ✅ Checklist de Implementación

- [ ] Crear modelo `PresentationLetterRequestModel`
- [ ] Crear migración de base de datos
- [ ] Crear serializers
- [ ] Crear ViewSet con acciones
- [ ] Registrar en URLs
- [ ] Crear servicio de generación de PDF
- [ ] Actualizar modelo `Practice` con FK
- [ ] Crear tests unitarios
- [ ] Actualizar documentación Swagger
- [ ] Notificar cambios al equipo frontend

---

## 🎨 Ejemplo de Uso Frontend

```javascript
// 1. Estudiante crea solicitud
const createLetterRequest = async () => {
  const response = await fetch('/api/v2/presentation-letters/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
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
  });
  
  const data = await response.json();
  // Estado: DRAFT
  return data;
};

// 2. Estudiante envía a secretaría
const submitRequest = async (id) => {
  await fetch(`/api/v2/presentation-letters/${id}/submit/`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  // Estado: PENDING
};

// 3. Secretaria aprueba
const approveRequest = async (id) => {
  await fetch(`/api/v2/presentation-letters/${id}/approve/`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  // Estado: APPROVED
};

// 4. Secretaria genera PDF
const generatePDF = async (id) => {
  await fetch(`/api/v2/presentation-letters/${id}/generate-pdf/`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  // Estado: GENERATED
};

// 5. Estudiante descarga
const downloadLetter = async (id) => {
  const response = await fetch(`/api/v2/presentation-letters/${id}/download/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const blob = await response.blob();
  // Descargar archivo
};
```

---

## 🚀 Próximos Pasos

1. **Crear la migración** del nuevo modelo
2. **Implementar generación de PDF** con plantilla oficial de la universidad
3. **Actualizar frontend** para usar el nuevo flujo
4. **Migrar prácticas existentes** (si aplica)
5. **Capacitar a secretarias** en el nuevo proceso

¿Deseas que proceda con la creación de estos archivos?
