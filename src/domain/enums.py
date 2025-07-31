"""
Enumeraciones para los roles del sistema de gestión de prácticas profesionales.
"""

from enum import Enum


class UserRole(Enum):
    """
    Roles disponibles en el sistema de gestión de prácticas profesionales.
    """
    PRACTICANTE = "PRACTICANTE"       # Estudiante realizando práctica
    SUPERVISOR = "SUPERVISOR"         # Supervisor de la empresa
    COORDINADOR = "COORDINADOR"       # Coordinador académico
    SECRETARIA = "SECRETARIA"         # Personal administrativo
    ADMINISTRADOR = "ADMINISTRADOR"   # Administrador del sistema

    def __str__(self):
        return self.value

    @classmethod
    def choices(cls):
        """Devuelve las opciones para usar en Django models."""
        return [(role.value, role.value) for role in cls]

    @classmethod
    def get_permissions(cls, role):
        """
        Define los permisos por rol.
        """
        permissions = {
            cls.PRACTICANTE: [
                'view_own_practice',
                'update_own_profile',
                'upload_documents',
                'view_company_info',
            ],
            cls.SUPERVISOR: [
                'view_assigned_practices',
                'evaluate_practices',
                'update_own_profile',
                'manage_company_offers',
                'view_company_reports',
            ],
            cls.COORDINADOR: [
                'view_all_practices',
                'assign_practices',
                'manage_companies',
                'generate_reports',
                'manage_students',
                'approve_practices',
            ],
            cls.SECRETARIA: [
                'view_all_practices',
                'manage_documents',
                'update_practice_status',
                'generate_basic_reports',
                'manage_notifications',
            ],
            cls.ADMINISTRADOR: [
                'full_system_access',
                'manage_users',
                'system_configuration',
                'view_system_logs',
                'manage_backups',
            ],
        }
        return permissions.get(role, [])

    @classmethod
    def can_access_practice(cls, user_role, practice_id, user_id):
        """
        Determina si un usuario puede acceder a una práctica específica.
        """
        if user_role in [cls.COORDINADOR, cls.SECRETARIA, cls.ADMINISTRADOR]:
            return True
        
        # Lógica específica para practicantes y supervisores
        # Esto se implementará en los servicios de dominio
        return False

    @classmethod
    def get_dashboard_permissions(cls, role):
        """
        Define qué secciones del dashboard puede ver cada rol.
        """
        dashboard_sections = {
            cls.PRACTICANTE: [
                'my_practice',
                'my_profile',
                'documents',
                'company_info',
                'notifications',
            ],
            cls.SUPERVISOR: [
                'assigned_practices',
                'evaluations',
                'company_management',
                'reports',
                'notifications',
            ],
            cls.COORDINADOR: [
                'all_practices',
                'students_management',
                'companies_management',
                'assignments',
                'reports',
                'analytics',
                'notifications',
            ],
            cls.SECRETARIA: [
                'practices_overview',
                'documents_management',
                'basic_reports',
                'notifications',
                'administrative_tasks',
            ],
            cls.ADMINISTRADOR: [
                'system_overview',
                'user_management',
                'system_configuration',
                'security_logs',
                'backups',
                'analytics',
                'all_reports',
            ],
        }
        return dashboard_sections.get(role, [])


class PracticeStatus(Enum):
    """Estados de las prácticas profesionales."""
    DRAFT = "DRAFT"                   # Borrador
    PENDING = "PENDING"               # Pendiente de aprobación
    APPROVED = "APPROVED"             # Aprobada
    IN_PROGRESS = "IN_PROGRESS"       # En progreso
    COMPLETED = "COMPLETED"           # Completada
    CANCELLED = "CANCELLED"           # Cancelada
    SUSPENDED = "SUSPENDED"           # Suspendida

    def __str__(self):
        return self.value

    @classmethod
    def choices(cls):
        return [(status.value, status.value) for status in cls]


class CompanyStatus(Enum):
    """Estados de las empresas."""
    PENDING_VALIDATION = "PENDING_VALIDATION"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    BLACKLISTED = "BLACKLISTED"

    def __str__(self):
        return self.value

    @classmethod
    def choices(cls):
        return [(status.value, status.value) for status in cls]


class DocumentType(Enum):
    """Tipos de documentos del sistema."""
    PRACTICE_AGREEMENT = "PRACTICE_AGREEMENT"
    EVALUATION_REPORT = "EVALUATION_REPORT"
    FINAL_REPORT = "FINAL_REPORT"
    COMPANY_VALIDATION = "COMPANY_VALIDATION"
    STUDENT_CV = "STUDENT_CV"
    ACADEMIC_RECORD = "ACADEMIC_RECORD"

    def __str__(self):
        return self.value

    @classmethod
    def choices(cls):
        return [(doc_type.value, doc_type.value) for doc_type in cls]
