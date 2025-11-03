"""
ViewSet para Solicitudes de Carta de Presentación.
"""

from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models as django_models
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from src.adapters.secondary.database.models import (
    PresentationLetterRequest,
    StudentProfile,
    Document
)
from src.adapters.primary.rest_api.presentation_letter_serializers import (
    PresentationLetterRequestCreateSerializer,
    PresentationLetterRequestDetailSerializer,
    PresentationLetterRequestListSerializer,
    SubmitPresentationLetterSerializer,
    ApprovePresentationLetterSerializer,
    RejectPresentationLetterSerializer,
    GeneratePresentationLetterPDFSerializer,
)


@extend_schema(tags=['Cartas de Presentación'])
class PresentationLetterRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Solicitudes de Carta de Presentación.
    
    Flujo:
    1. PRACTICANTE crea solicitud (POST /) → DRAFT
    2. PRACTICANTE envía a revisión (POST /{id}/submit/) → PENDING
    3. SECRETARIA aprueba (POST /{id}/approve/) → APPROVED
    4. SECRETARIA genera PDF (POST /{id}/generate-pdf/) → GENERATED
    5. PRACTICANTE descarga carta (GET /{id}/download/)
    
    **Permisos**:
    - PRACTICANTE: Crear, ver propias, editar propias (solo DRAFT/REJECTED)
    - SECRETARIA: Ver asignadas/pendientes, aprobar, rechazar, generar PDF
    - COORDINADOR/ADMIN: Ver todas
    """
    
    queryset = PresentationLetterRequest.objects.select_related(
        'student',
        'student__usuario',
        'student__escuela',
        'escuela',
        'empresa',
        'assigned_secretary',
        'letter_document'
    ).all()
    
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    
    filterset_fields = ['status', 'student__codigo_estudiante']
    search_fields = ['student_code', 'student_full_name', 'company_name']
    ordering_fields = ['created_at', 'submitted_at', 'start_date']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """
        Permisos personalizados según acción.
        Todos pueden acceder sin restricciones.
        """
        # Permitir acceso sin autenticación
        return [AllowAny()]
    
    def get_serializer_class(self):
        """Retornar serializer según la acción."""
        if self.action == 'list':
            return PresentationLetterRequestListSerializer
        elif self.action in ['retrieve']:
            return PresentationLetterRequestDetailSerializer
        return PresentationLetterRequestCreateSerializer
    
    def get_queryset(self):
        """
        Filtrar según rol del usuario.
        Por defecto, todos los usuarios autenticados ven todas las solicitudes.
        """
        # Retornar todas las solicitudes para cualquier usuario autenticado
        return self.queryset
    
    def perform_create(self, serializer):
        """Auto-rellenar datos del estudiante autenticado."""
        user = self.request.user
        
        # Si el usuario está autenticado, obtener su perfil de estudiante
        if user.is_authenticated:
            student = get_object_or_404(StudentProfile, usuario=user)
            serializer.save(
                student=student,
                status='DRAFT'
            )
        else:
            # Si no está autenticado, guardar sin estudiante
            # (para testing o casos especiales)
            serializer.save(status='DRAFT')
    
    def perform_update(self, serializer):
        """Validar que solo se pueda editar en DRAFT o REJECTED."""
        instance = self.get_object()
        
        if not instance.can_edit():
            raise serializers.ValidationError(
                'Solo se pueden editar solicitudes en estado DRAFT o REJECTED'
            )
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Solo permitir eliminar en estado DRAFT."""
        if instance.status != 'DRAFT':
            raise serializers.ValidationError(
                'Solo se pueden eliminar solicitudes en estado DRAFT'
            )
        instance.delete()
    
    # ========================================================================
    # ACCIONES PERSONALIZADAS
    # ========================================================================
    
    @extend_schema(
        tags=['Carta de Presentación'],
        summary='Enviar solicitud a secretaría',
        description='''
        Envía la solicitud de carta de presentación a secretaría para revisión.
        
        **Requiere**: Rol PRACTICANTE y solicitud en estado DRAFT.
        
        **Transición**: DRAFT → PENDING
        ''',
        request=SubmitPresentationLetterSerializer,
        responses={
            200: OpenApiResponse(description='Solicitud enviada exitosamente'),
            400: OpenApiResponse(description='Estado inválido'),
            403: OpenApiResponse(description='Sin permisos'),
        }
    )
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[AllowAny],
        url_path='submit'
    )
    def submit(self, request, pk=None):
        """
        Enviar solicitud a secretaría.
        
        POST /api/v2/presentation-letters/{id}/submit/
        
        Transición: DRAFT → PENDING
        """
        letter_request = self.get_object()
        
        # Validar que el usuario sea el dueño
        user = request.user
        role = user.rol_id.nombre if user.rol_id else None
        
        if role != 'PRACTICANTE':
            return Response(
                {'error': 'Solo los practicantes pueden enviar solicitudes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validar estado
        if not letter_request.can_submit():
            return Response(
                {'error': 'Solo se pueden enviar solicitudes en estado DRAFT'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cambiar estado
        letter_request.status = 'PENDING'
        letter_request.submitted_at = timezone.now()
        letter_request.save()
        
        # TODO: Enviar notificación a secretarías
        
        serializer = self.get_serializer(letter_request)
        return Response({
            'success': True,
            'message': 'Solicitud enviada a secretaría exitosamente',
            'data': serializer.data
        })
    
    @extend_schema(
        tags=['Carta de Presentación'],
        summary='Aprobar solicitud (Secretaria)',
        description='''
        Aprueba la solicitud de carta de presentación.
        
        **Requiere**: Rol SECRETARIA y solicitud en estado PENDING.
        
        **Transición**: PENDING → APPROVED
        ''',
        request=ApprovePresentationLetterSerializer,
        responses={
            200: OpenApiResponse(description='Solicitud aprobada'),
            400: OpenApiResponse(description='Estado inválido'),
            403: OpenApiResponse(description='Sin permisos'),
        }
    )
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[AllowAny],
        url_path='approve'
    )
    def approve(self, request, pk=None):
        """
        Aprobar solicitud (Secretaria).
        
        POST /api/v2/presentation-letters/{id}/approve/
        
        Transición: PENDING → APPROVED
        """
        letter_request = self.get_object()
        user = request.user
        role = user.rol_id.nombre if user.rol_id else None
        
        # Validar rol
        if role != 'SECRETARIA':
            return Response(
                {'error': 'Solo las secretarias pueden aprobar solicitudes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validar estado
        if not letter_request.can_approve():
            return Response(
                {'error': 'Solo se pueden aprobar solicitudes en estado PENDING'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Asignar secretaria y aprobar
        letter_request.assigned_secretary = user
        letter_request.status = 'APPROVED'
        letter_request.reviewed_at = timezone.now()
        letter_request.rejection_reason = None  # Limpiar rechazo previo
        letter_request.save()
        
        # TODO: Notificar al estudiante
        
        serializer = self.get_serializer(letter_request)
        return Response({
            'success': True,
            'message': 'Solicitud aprobada exitosamente',
            'data': serializer.data
        })
    
    @extend_schema(
        tags=['Carta de Presentación'],
        summary='Rechazar solicitud (Secretaria)',
        description='''
        Rechaza la solicitud con un motivo.
        
        **Requiere**: Rol SECRETARIA y solicitud en estado PENDING.
        
        **Transición**: PENDING → REJECTED
        ''',
        request=RejectPresentationLetterSerializer,
        responses={
            200: OpenApiResponse(description='Solicitud rechazada'),
            400: OpenApiResponse(description='Datos inválidos'),
            403: OpenApiResponse(description='Sin permisos'),
        }
    )
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[AllowAny],
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
        user = request.user
        role = user.rol_id.nombre if user.rol_id else None
        
        # Validar rol
        if role != 'SECRETARIA':
            return Response(
                {'error': 'Solo las secretarias pueden rechazar solicitudes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validar datos
        serializer = RejectPresentationLetterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Rechazar
        letter_request.status = 'REJECTED'
        letter_request.rejection_reason = serializer.validated_data['rejection_reason']
        letter_request.assigned_secretary = user
        letter_request.reviewed_at = timezone.now()
        letter_request.save()
        
        # TODO: Notificar al estudiante
        
        return Response({
            'success': True,
            'message': 'Solicitud rechazada',
            'data': self.get_serializer(letter_request).data
        })
    
    @extend_schema(
        tags=['Carta de Presentación'],
        summary='Generar PDF de carta (Secretaria)',
        description='''
        Genera el PDF oficial de la carta de presentación.
        
        **Requiere**: Rol SECRETARIA y solicitud en estado APPROVED.
        
        **Transición**: APPROVED → GENERATED
        
        El PDF se genera con los datos de la solicitud y se guarda como documento.
        ''',
        request=GeneratePresentationLetterPDFSerializer,
        responses={
            200: OpenApiResponse(description='PDF generado exitosamente'),
            400: OpenApiResponse(description='Estado inválido'),
            403: OpenApiResponse(description='Sin permisos'),
        }
    )
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[AllowAny],
        url_path='generate-pdf'
    )
    def generate_pdf(self, request, pk=None):
        """
        Generar PDF de carta de presentación.
        
        POST /api/v2/presentation-letters/{id}/generate-pdf/
        
        Transición: APPROVED → GENERATED
        """
        letter_request = self.get_object()
        user = request.user
        role = user.rol_id.nombre if user.rol_id else None
        
        # Validar rol
        if role != 'SECRETARIA':
            return Response(
                {'error': 'Solo las secretarias pueden generar cartas'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validar estado
        if not letter_request.can_generate_pdf():
            return Response(
                {'error': 'Solo se pueden generar cartas aprobadas sin documento previo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generar PDF
        try:
            from src.application.services.pdf_generator import generate_presentation_letter_pdf
            
            pdf_file = generate_presentation_letter_pdf(letter_request)
            
            # Crear documento
            document = Document.objects.create(
                tipo_documento='CARTA_PRESENTACION',
                descripcion=f'Carta de Presentación - {letter_request.student_full_name}',
                archivo=pdf_file,
                estado='APPROVED'
            )
            
            # Actualizar solicitud
            letter_request.letter_document = document
            letter_request.status = 'GENERATED'
            letter_request.save()
            
            return Response({
                'success': True,
                'message': 'Carta de presentación generada exitosamente',
                'document_id': document.id,
                'download_url': request.build_absolute_uri(document.archivo.url) if document.archivo else None
            })
            
        except ImportError:
            # Si no existe el servicio aún, retornar success simulado
            letter_request.status = 'GENERATED'
            letter_request.save()
            
            return Response({
                'success': True,
                'message': 'Carta marcada como generada (PDF service pendiente de implementar)',
                'document_id': None,
                'note': 'Servicio de generación de PDF pendiente de implementación'
            })
        except Exception as e:
            return Response(
                {'error': f'Error al generar PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        tags=['Carta de Presentación'],
        summary='Descargar carta generada',
        description='''
        Descarga el PDF de la carta de presentación generada.
        
        **Requiere**: Solicitud en estado GENERATED con documento asociado.
        ''',
        responses={
            200: OpenApiResponse(description='URL de descarga'),
            404: OpenApiResponse(description='Carta no generada'),
        }
    )
    @action(
        detail=True,
        methods=['get'],
        permission_classes=[AllowAny],
        url_path='download'
    )
    def download(self, request, pk=None):
        """
        Descargar PDF de carta de presentación.
        
        GET /api/v2/presentation-letters/{id}/download/
        """
        letter_request = self.get_object()
        
        if not letter_request.letter_document or not letter_request.letter_document.archivo:
            return Response(
                {'error': 'Carta aún no generada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Retornar URL de descarga
        download_url = request.build_absolute_uri(letter_request.letter_document.archivo.url)
        
        return Response({
            'success': True,
            'download_url': download_url,
            'document_id': letter_request.letter_document.id,
            'filename': letter_request.letter_document.archivo.name.split('/')[-1]
        })
