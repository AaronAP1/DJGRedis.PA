"""
Serializers para Solicitud de Carta de Presentación.
"""

from rest_framework import serializers
from src.adapters.secondary.database.models import (
    PresentationLetterRequest, 
    StudentProfile,
    School,
    Company
)


class PresentationLetterRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear/actualizar solicitud de carta de presentación.
    
    Los datos del estudiante se auto-rellenan desde el usuario autenticado.
    Permite seleccionar escuela y empresa existentes mediante IDs.
    """
    
    # Campos de solo lectura
    status = serializers.CharField(read_only=True)
    
    # NUEVOS: IDs para relaciones
    escuela_id = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(estado='ACTIVO'),
        source='escuela',
        required=True,
        help_text='ID de la escuela profesional'
    )
    
    empresa_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.filter(estado='ACTIVO'),
        source='empresa',
        required=True,
        help_text='ID de la empresa'
    )
    
    class Meta:
        model = PresentationLetterRequest
        fields = [
            'id',
            # Relaciones
            'escuela_id',
            'empresa_id',
            # Datos del estudiante
            'student_full_name',
            'student_code',
            'student_email',
            'year_of_study',
            'study_cycle',
            # Datos de la empresa
            'company_representative',
            'company_position',
            'company_phone',
            'practice_area',
            'start_date',
            # Metadatos
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'created_at',
            'updated_at',
        ]
    
    def validate_year_of_study(self, value):
        """Validar año de estudios."""
        valid_years = [
            'Primer año',
            'Segundo año',
            'Tercer año',
            'Cuarto año',
            'Quinto año',
            'Sexto año'
        ]
        if value not in valid_years:
            raise serializers.ValidationError(
                f"Año de estudios debe ser uno de: {', '.join(valid_years)}"
            )
        return value
    
    def validate_study_cycle(self, value):
        """Validar ciclo de estudios."""
        import re
        if not re.match(r'^[IVX]+$', value):
            raise serializers.ValidationError(
                "Ciclo debe estar en números romanos (ej: IX, X, XI)"
            )
        return value
    
    def validate(self, attrs):
        """Validaciones generales."""
        # Verificar que la fecha de inicio no sea pasada
        from datetime import date
        if 'start_date' in attrs and attrs['start_date'] < date.today():
            raise serializers.ValidationError({
                'start_date': 'La fecha de inicio no puede ser en el pasado'
            })
        
        # Si no se proporciona empresa_id, validar que se proporcionen datos manuales
        if not attrs.get('empresa') and not self.initial_data.get('company_name'):
            raise serializers.ValidationError({
                'empresa_id': 'Debe seleccionar una empresa existente o proporcionar company_name manualmente'
            })
        
        return attrs


class PresentationLetterRequestDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado incluyendo relaciones."""
    
    # Usar SerializerMethodField para evitar importaciones circulares
    student_info = serializers.SerializerMethodField()
    escuela_info = serializers.SerializerMethodField()
    empresa_info = serializers.SerializerMethodField()
    secretary_info = serializers.SerializerMethodField()
    letter_document_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PresentationLetterRequest
        fields = '__all__'
    
    def get_student_info(self, obj):
        """Retorna información básica del estudiante."""
        if obj.student_id:
            try:
                return {
                    'id': obj.student.id,
                    'codigo': obj.student.codigo,
                    'nombres': obj.student.usuario.nombres,
                    'apellidos': obj.student.usuario.apellidos,
                    'email': obj.student.usuario.correo,
                }
            except:
                return None
        return None
    
    def get_escuela_info(self, obj):
        """Retorna información de la escuela profesional."""
        if obj.escuela:
            return {
                'id': obj.escuela.id,
                'nombre': obj.escuela.nombre,
                'codigo': obj.escuela.codigo,
            }
        return None
    
    def get_empresa_info(self, obj):
        """Retorna información de la empresa."""
        if obj.empresa:
            return {
                'id': obj.empresa.id,
                'nombre': obj.empresa.nombre,
                'ruc': obj.empresa.ruc,
                'razon_social': obj.empresa.razon_social,
                'direccion': obj.empresa.direccion,
                'telefono': obj.empresa.telefono,
                'correo': obj.empresa.correo,
                'sector_economico': obj.empresa.sector_economico,
            }
        return None
    
    def get_secretary_info(self, obj):
        """Retorna información básica de la secretaria."""
        if obj.assigned_secretary:
            return {
                'id': obj.assigned_secretary.id,
                'nombres': obj.assigned_secretary.nombres,
                'apellidos': obj.assigned_secretary.apellidos,
                'email': obj.assigned_secretary.correo,
            }
        return None
    
    def get_letter_document_url(self, obj):
        """Retorna URL del documento si existe."""
        if obj.letter_document and obj.letter_document.archivo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.letter_document.archivo.url)
        return None


class PresentationLetterRequestListSerializer(serializers.ModelSerializer):
    """Serializer para listado resumido."""
    
    student_name = serializers.CharField(source='student_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    secretary_name = serializers.SerializerMethodField()
    escuela_nombre = serializers.CharField(source='escuela.nombre', read_only=True, allow_null=True)
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True, allow_null=True)
    
    class Meta:
        model = PresentationLetterRequest
        fields = [
            'id',
            'student_code',
            'student_name',
            'escuela_nombre',
            'empresa_nombre',
            'practice_area',
            'start_date',
            'status',
            'status_display',
            'secretary_name',
            'created_at',
            'submitted_at',
            'reviewed_at',
        ]
    
    def get_secretary_name(self, obj):
        """Retorna nombre de la secretaria asignada."""
        if obj.assigned_secretary:
            return f"{obj.assigned_secretary.nombres} {obj.assigned_secretary.apellidos}"
        return None


class SubmitPresentationLetterSerializer(serializers.Serializer):
    """Serializer para enviar solicitud a secretaría."""
    # No requiere datos adicionales
    pass


class ApprovePresentationLetterSerializer(serializers.Serializer):
    """Serializer para aprobar solicitud (Secretaria)."""
    # No requiere datos adicionales
    pass


class RejectPresentationLetterSerializer(serializers.Serializer):
    """Serializer para rechazar solicitud."""
    rejection_reason = serializers.CharField(
        required=True,
        max_length=500,
        help_text="Motivo del rechazo (mínimo 10 caracteres)",
        min_length=10
    )


class GeneratePresentationLetterPDFSerializer(serializers.Serializer):
    """Serializer para generar PDF de carta."""
    # No requiere datos adicionales
    pass
