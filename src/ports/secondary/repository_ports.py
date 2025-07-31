"""
Puertos secundarios - Interfaces para servicios externos.
Definen las operaciones que el sistema necesita del mundo exterior.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Generic, TypeVar
from uuid import UUID
from datetime import datetime

from src.domain.entities import User, Student, Practice, Company, Supervisor, Document, Notification
from src.domain.enums import UserRole, PracticeStatus

T = TypeVar('T')


class Repository(ABC, Generic[T]):
    """Repositorio base genérico."""

    @abstractmethod
    async def save(self, entity: T) -> T:
        """Guarda una entidad."""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Obtiene una entidad por ID."""
        pass

    @abstractmethod
    async def get_all(self) -> List[T]:
        """Obtiene todas las entidades."""
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Actualiza una entidad."""
        pass

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Elimina una entidad."""
        pass

    @abstractmethod
    async def exists(self, entity_id: UUID) -> bool:
        """Verifica si existe una entidad."""
        pass


class UserRepositoryPort(Repository[User]):
    """Puerto del repositorio de usuarios."""

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Obtiene un usuario por email."""
        pass

    @abstractmethod
    async def get_by_role(self, role: UserRole) -> List[User]:
        """Obtiene usuarios por rol."""
        pass

    @abstractmethod
    async def search_by_name(self, name: str) -> List[User]:
        """Busca usuarios por nombre."""
        pass

    @abstractmethod
    async def get_active_users(self) -> List[User]:
        """Obtiene usuarios activos."""
        pass


class StudentRepositoryPort(Repository[Student]):
    """Puerto del repositorio de estudiantes."""

    @abstractmethod
    async def get_by_codigo(self, codigo: str) -> Optional[Student]:
        """Obtiene un estudiante por código."""
        pass

    @abstractmethod
    async def get_by_documento(self, documento: str) -> Optional[Student]:
        """Obtiene un estudiante por documento."""
        pass

    @abstractmethod
    async def get_eligible_for_practice(self) -> List[Student]:
        """Obtiene estudiantes elegibles para práctica."""
        pass

    @abstractmethod
    async def search_by_criteria(self, criteria: Dict[str, Any]) -> List[Student]:
        """Busca estudiantes por criterios."""
        pass


class CompanyRepositoryPort(Repository[Company]):
    """Puerto del repositorio de empresas."""

    @abstractmethod
    async def get_by_ruc(self, ruc: str) -> Optional[Company]:
        """Obtiene una empresa por RUC."""
        pass

    @abstractmethod
    async def get_by_status(self, status: str) -> List[Company]:
        """Obtiene empresas por estado."""
        pass

    @abstractmethod
    async def search_by_name(self, name: str) -> List[Company]:
        """Busca empresas por nombre."""
        pass

    @abstractmethod
    async def get_active_companies(self) -> List[Company]:
        """Obtiene empresas activas."""
        pass


class SupervisorRepositoryPort(Repository[Supervisor]):
    """Puerto del repositorio de supervisores."""

    @abstractmethod
    async def get_by_company(self, company_id: UUID) -> List[Supervisor]:
        """Obtiene supervisores de una empresa."""
        pass

    @abstractmethod
    async def get_by_documento(self, documento: str) -> Optional[Supervisor]:
        """Obtiene un supervisor por documento."""
        pass


class PracticeRepositoryPort(Repository[Practice]):
    """Puerto del repositorio de prácticas."""

    @abstractmethod
    async def get_by_student(self, student_id: UUID) -> List[Practice]:
        """Obtiene prácticas de un estudiante."""
        pass

    @abstractmethod
    async def get_by_company(self, company_id: UUID) -> List[Practice]:
        """Obtiene prácticas de una empresa."""
        pass

    @abstractmethod
    async def get_by_supervisor(self, supervisor_id: UUID) -> List[Practice]:
        """Obtiene prácticas de un supervisor."""
        pass

    @abstractmethod
    async def get_by_status(self, status: PracticeStatus) -> List[Practice]:
        """Obtiene prácticas por estado."""
        pass

    @abstractmethod
    async def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Practice]:
        """Obtiene prácticas en un rango de fechas."""
        pass

    @abstractmethod
    async def search_with_filters(self, filters: Dict[str, Any]) -> List[Practice]:
        """Busca prácticas con filtros."""
        pass


class DocumentRepositoryPort(Repository[Document]):
    """Puerto del repositorio de documentos."""

    @abstractmethod
    async def get_by_practice(self, practice_id: UUID) -> List[Document]:
        """Obtiene documentos de una práctica."""
        pass

    @abstractmethod
    async def get_by_type(self, document_type: str) -> List[Document]:
        """Obtiene documentos por tipo."""
        pass

    @abstractmethod
    async def get_pending_approval(self) -> List[Document]:
        """Obtiene documentos pendientes de aprobación."""
        pass


class NotificationRepositoryPort(Repository[Notification]):
    """Puerto del repositorio de notificaciones."""

    @abstractmethod
    async def get_by_user(self, user_id: UUID) -> List[Notification]:
        """Obtiene notificaciones de un usuario."""
        pass

    @abstractmethod
    async def get_unread_by_user(self, user_id: UUID) -> List[Notification]:
        """Obtiene notificaciones no leídas de un usuario."""
        pass

    @abstractmethod
    async def mark_as_read(self, notification_id: UUID) -> bool:
        """Marca una notificación como leída."""
        pass

    @abstractmethod
    async def mark_all_as_read(self, user_id: UUID) -> bool:
        """Marca todas las notificaciones como leídas."""
        pass


class CacheServicePort(ABC):
    """Puerto para servicio de caché."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Establece un valor en el caché."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Elimina un valor del caché."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Verifica si existe una clave en el caché."""
        pass

    @abstractmethod
    async def clear_pattern(self, pattern: str) -> bool:
        """Elimina claves que coincidan con un patrón."""
        pass


class EmailServicePort(ABC):
    """Puerto para servicio de email."""

    @abstractmethod
    async def send_email(self, to: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Envía un email."""
        pass

    @abstractmethod
    async def send_bulk_email(self, recipients: List[str], subject: str, body: str) -> bool:
        """Envía emails masivos."""
        pass

    @abstractmethod
    async def send_template_email(self, to: str, template_name: str, context: Dict[str, Any]) -> bool:
        """Envía un email usando una plantilla."""
        pass


class FileStoragePort(ABC):
    """Puerto para almacenamiento de archivos."""

    @abstractmethod
    async def save_file(self, file_content: bytes, file_name: str, folder: str) -> str:
        """Guarda un archivo y retorna la ruta."""
        pass

    @abstractmethod
    async def get_file(self, file_path: str) -> Optional[bytes]:
        """Obtiene el contenido de un archivo."""
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Elimina un archivo."""
        pass

    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """Verifica si existe un archivo."""
        pass

    @abstractmethod
    async def get_file_url(self, file_path: str) -> str:
        """Obtiene la URL de un archivo."""
        pass


class SearchServicePort(ABC):
    """Puerto para servicio de búsqueda."""

    @abstractmethod
    async def index_document(self, index: str, document: Dict[str, Any]) -> bool:
        """Indexa un documento."""
        pass

    @abstractmethod
    async def search_documents(self, index: str, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Busca documentos."""
        pass

    @abstractmethod
    async def delete_document(self, index: str, document_id: str) -> bool:
        """Elimina un documento del índice."""
        pass

    @abstractmethod
    async def bulk_index(self, index: str, documents: List[Dict[str, Any]]) -> bool:
        """Indexa múltiples documentos."""
        pass


class TaskQueuePort(ABC):
    """Puerto para cola de tareas asíncronas."""

    @abstractmethod
    async def enqueue_task(self, task_name: str, args: Dict[str, Any], delay: Optional[int] = None) -> str:
        """Encola una tarea."""
        pass

    @abstractmethod
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado de una tarea."""
        pass

    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """Cancela una tarea."""
        pass


class SecurityServicePort(ABC):
    """Puerto para servicios de seguridad."""

    @abstractmethod
    async def hash_password(self, password: str) -> str:
        """Hashea una contraseña."""
        pass

    @abstractmethod
    async def verify_password(self, password: str, hashed: str) -> bool:
        """Verifica una contraseña."""
        pass

    @abstractmethod
    async def generate_token(self, payload: Dict[str, Any]) -> str:
        """Genera un token JWT."""
        pass

    @abstractmethod
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verifica un token JWT."""
        pass

    @abstractmethod
    async def encrypt_data(self, data: str) -> str:
        """Encripta datos sensibles."""
        pass

    @abstractmethod
    async def decrypt_data(self, encrypted_data: str) -> str:
        """Desencripta datos."""
        pass


class LoggingServicePort(ABC):
    """Puerto para servicio de logging."""

    @abstractmethod
    async def log_info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Registra un log de información."""
        pass

    @abstractmethod
    async def log_warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Registra un log de advertencia."""
        pass

    @abstractmethod
    async def log_error(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Registra un log de error."""
        pass

    @abstractmethod
    async def log_security_event(self, event: str, user_id: Optional[UUID] = None, context: Optional[Dict[str, Any]] = None) -> None:
        """Registra un evento de seguridad."""
        pass


class MonitoringServicePort(ABC):
    """Puerto para servicio de monitoreo."""

    @abstractmethod
    async def record_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Registra una métrica."""
        pass

    @abstractmethod
    async def increment_counter(self, counter_name: str, tags: Optional[Dict[str, str]] = None) -> None:
        """Incrementa un contador."""
        pass

    @abstractmethod
    async def record_timing(self, operation_name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Registra el tiempo de una operación."""
        pass
