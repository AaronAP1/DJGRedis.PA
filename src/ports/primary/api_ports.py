"""
Puertos primarios - Interfaces de entrada al sistema.
Definen las operaciones que el sistema expone al mundo exterior.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from src.domain.entities import User, Student, Practice, Company, Supervisor, Document
from src.domain.enums import UserRole, PracticeStatus
from src.domain.value_objects import Email, Documento, Periodo


class AuthenticationPort(ABC):
    """Puerto para operaciones de autenticación."""

    @abstractmethod
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Autentica un usuario con email y contraseña."""
        pass

    @abstractmethod
    async def register_user(self, user_data: Dict[str, Any]) -> User:
        """Registra un nuevo usuario en el sistema."""
        pass

    @abstractmethod
    async def generate_tokens(self, user: User) -> Dict[str, str]:
        """Genera tokens JWT para el usuario."""
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Dict[str, str]:
        """Refresca el token de acceso."""
        pass

    @abstractmethod
    async def logout_user(self, user_id: UUID) -> bool:
        """Cierra sesión del usuario."""
        pass

    @abstractmethod
    async def change_password(self, user_id: UUID, old_password: str, new_password: str) -> bool:
        """Cambia la contraseña del usuario."""
        pass

    @abstractmethod
    async def reset_password(self, email: str) -> bool:
        """Inicia el proceso de reset de contraseña."""
        pass


class UserManagementPort(ABC):
    """Puerto para gestión de usuarios."""

    @abstractmethod
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Crea un nuevo usuario."""
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Obtiene un usuario por su ID."""
        pass

    @abstractmethod
    async def get_user_by_email(self, email: Email) -> Optional[User]:
        """Obtiene un usuario por su email."""
        pass

    @abstractmethod
    async def update_user(self, user_id: UUID, update_data: Dict[str, Any]) -> User:
        """Actualiza los datos de un usuario."""
        pass

    @abstractmethod
    async def deactivate_user(self, user_id: UUID) -> bool:
        """Desactiva un usuario."""
        pass

    @abstractmethod
    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """Obtiene todos los usuarios de un rol específico."""
        pass

    @abstractmethod
    async def search_users(self, query: str, role: Optional[UserRole] = None) -> List[User]:
        """Busca usuarios por nombre, email, etc."""
        pass


class StudentManagementPort(ABC):
    """Puerto para gestión de estudiantes."""

    @abstractmethod
    async def create_student(self, student_data: Dict[str, Any]) -> Student:
        """Crea un nuevo estudiante."""
        pass

    @abstractmethod
    async def get_student_by_id(self, student_id: UUID) -> Optional[Student]:
        """Obtiene un estudiante por su ID."""
        pass

    @abstractmethod
    async def get_student_by_code(self, codigo: str) -> Optional[Student]:
        """Obtiene un estudiante por su código."""
        pass

    @abstractmethod
    async def update_student(self, student_id: UUID, update_data: Dict[str, Any]) -> Student:
        """Actualiza los datos de un estudiante."""
        pass

    @abstractmethod
    async def get_eligible_students(self) -> List[Student]:
        """Obtiene estudiantes elegibles para prácticas."""
        pass

    @abstractmethod
    async def search_students(self, query: str) -> List[Student]:
        """Busca estudiantes por código, nombre, carrera, etc."""
        pass


class CompanyManagementPort(ABC):
    """Puerto para gestión de empresas."""

    @abstractmethod
    async def create_company(self, company_data: Dict[str, Any]) -> Company:
        """Crea una nueva empresa."""
        pass

    @abstractmethod
    async def get_company_by_id(self, company_id: UUID) -> Optional[Company]:
        """Obtiene una empresa por su ID."""
        pass

    @abstractmethod
    async def get_company_by_ruc(self, ruc: str) -> Optional[Company]:
        """Obtiene una empresa por su RUC."""
        pass

    @abstractmethod
    async def update_company(self, company_id: UUID, update_data: Dict[str, Any]) -> Company:
        """Actualiza los datos de una empresa."""
        pass

    @abstractmethod
    async def validate_company(self, company_id: UUID) -> Company:
        """Valida una empresa para recibir practicantes."""
        pass

    @abstractmethod
    async def suspend_company(self, company_id: UUID, motivo: str) -> Company:
        """Suspende una empresa."""
        pass

    @abstractmethod
    async def get_active_companies(self) -> List[Company]:
        """Obtiene todas las empresas activas."""
        pass

    @abstractmethod
    async def search_companies(self, query: str) -> List[Company]:
        """Busca empresas por nombre, sector, etc."""
        pass


class PracticeManagementPort(ABC):
    """Puerto para gestión de prácticas profesionales."""

    @abstractmethod
    async def create_practice(self, practice_data: Dict[str, Any]) -> Practice:
        """Crea una nueva práctica."""
        pass

    @abstractmethod
    async def get_practice_by_id(self, practice_id: UUID) -> Optional[Practice]:
        """Obtiene una práctica por su ID."""
        pass

    @abstractmethod
    async def update_practice(self, practice_id: UUID, update_data: Dict[str, Any]) -> Practice:
        """Actualiza los datos de una práctica."""
        pass

    @abstractmethod
    async def assign_supervisor(self, practice_id: UUID, supervisor_id: UUID) -> Practice:
        """Asigna un supervisor a una práctica."""
        pass

    @abstractmethod
    async def approve_practice(self, practice_id: UUID, approved_by: UUID) -> Practice:
        """Aprueba una práctica."""
        pass

    @abstractmethod
    async def start_practice(self, practice_id: UUID) -> Practice:
        """Inicia una práctica."""
        pass

    @abstractmethod
    async def complete_practice(self, practice_id: UUID, evaluation_data: Dict[str, Any]) -> Practice:
        """Completa una práctica con evaluación."""
        pass

    @abstractmethod
    async def cancel_practice(self, practice_id: UUID, motivo: str) -> Practice:
        """Cancela una práctica."""
        pass

    @abstractmethod
    async def get_practices_by_student(self, student_id: UUID) -> List[Practice]:
        """Obtiene las prácticas de un estudiante."""
        pass

    @abstractmethod
    async def get_practices_by_supervisor(self, supervisor_id: UUID) -> List[Practice]:
        """Obtiene las prácticas supervisadas por un supervisor."""
        pass

    @abstractmethod
    async def get_practices_by_company(self, company_id: UUID) -> List[Practice]:
        """Obtiene las prácticas de una empresa."""
        pass

    @abstractmethod
    async def get_practices_by_status(self, status: PracticeStatus) -> List[Practice]:
        """Obtiene prácticas por estado."""
        pass

    @abstractmethod
    async def search_practices(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Practice]:
        """Busca prácticas con filtros."""
        pass


class DocumentManagementPort(ABC):
    """Puerto para gestión de documentos."""

    @abstractmethod
    async def upload_document(self, document_data: Dict[str, Any]) -> Document:
        """Sube un documento al sistema."""
        pass

    @abstractmethod
    async def get_document_by_id(self, document_id: UUID) -> Optional[Document]:
        """Obtiene un documento por su ID."""
        pass

    @abstractmethod
    async def get_documents_by_practice(self, practice_id: UUID) -> List[Document]:
        """Obtiene todos los documentos de una práctica."""
        pass

    @abstractmethod
    async def approve_document(self, document_id: UUID, approved_by: UUID) -> Document:
        """Aprueba un documento."""
        pass

    @abstractmethod
    async def reject_document(self, document_id: UUID, rejected_by: UUID, motivo: str) -> Document:
        """Rechaza un documento."""
        pass

    @abstractmethod
    async def delete_document(self, document_id: UUID) -> bool:
        """Elimina un documento."""
        pass

    @abstractmethod
    async def download_document(self, document_id: UUID) -> Dict[str, Any]:
        """Descarga un documento."""
        pass


class ReportingPort(ABC):
    """Puerto para generación de reportes."""

    @abstractmethod
    async def generate_practice_report(self, practice_id: UUID) -> Dict[str, Any]:
        """Genera reporte de una práctica específica."""
        pass

    @abstractmethod
    async def generate_student_report(self, student_id: UUID) -> Dict[str, Any]:
        """Genera reporte de un estudiante."""
        pass

    @abstractmethod
    async def generate_company_report(self, company_id: UUID) -> Dict[str, Any]:
        """Genera reporte de una empresa."""
        pass

    @abstractmethod
    async def generate_period_report(self, periodo: Periodo) -> Dict[str, Any]:
        """Genera reporte de un periodo específico."""
        pass

    @abstractmethod
    async def generate_statistics_report(self) -> Dict[str, Any]:
        """Genera reporte de estadísticas generales."""
        pass

    @abstractmethod
    async def export_report_pdf(self, report_data: Dict[str, Any]) -> bytes:
        """Exporta un reporte a PDF."""
        pass

    @abstractmethod
    async def export_report_excel(self, report_data: Dict[str, Any]) -> bytes:
        """Exporta un reporte a Excel."""
        pass


class NotificationPort(ABC):
    """Puerto para gestión de notificaciones."""

    @abstractmethod
    async def send_notification(self, user_id: UUID, notification_data: Dict[str, Any]) -> bool:
        """Envía una notificación a un usuario."""
        pass

    @abstractmethod
    async def send_bulk_notification(self, user_ids: List[UUID], notification_data: Dict[str, Any]) -> bool:
        """Envía notificaciones masivas."""
        pass

    @abstractmethod
    async def get_user_notifications(self, user_id: UUID, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Obtiene las notificaciones de un usuario."""
        pass

    @abstractmethod
    async def mark_notification_read(self, notification_id: UUID) -> bool:
        """Marca una notificación como leída."""
        pass

    @abstractmethod
    async def mark_all_notifications_read(self, user_id: UUID) -> bool:
        """Marca todas las notificaciones de un usuario como leídas."""
        pass
