"""
Data Transfer Objects (DTOs) para la comunicación entre capas.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


@dataclass
class UserDTO:
    """DTO para Usuario."""
    id: Optional[UUID] = None
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    role: str = ""
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


@dataclass
class StudentDTO:
    """DTO para Estudiante."""
    id: Optional[UUID] = None
    user: Optional[UserDTO] = None
    codigo_estudiante: str = ""
    documento_numero: str = ""
    documento_tipo: str = ""
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    carrera: Optional[str] = None
    semestre_actual: Optional[int] = None
    promedio_ponderado: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class CompanyDTO:
    """DTO para Empresa."""
    id: Optional[UUID] = None
    ruc: str = ""
    razon_social: str = ""
    nombre_comercial: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    sector_economico: Optional[str] = None
    tamaño_empresa: Optional[str] = None
    status: str = "PENDING_VALIDATION"
    fecha_validacion: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def nombre_display(self) -> str:
        return self.nombre_comercial or self.razon_social


@dataclass
class SupervisorDTO:
    """DTO para Supervisor."""
    id: Optional[UUID] = None
    user: Optional[UserDTO] = None
    company: Optional[CompanyDTO] = None
    documento_numero: str = ""
    documento_tipo: str = ""
    cargo: str = ""
    telefono: Optional[str] = None
    años_experiencia: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class PracticeDTO:
    """DTO para Práctica."""
    id: Optional[UUID] = None
    student: Optional[StudentDTO] = None
    company: Optional[CompanyDTO] = None
    supervisor: Optional[SupervisorDTO] = None
    titulo: str = ""
    descripcion: str = ""
    objetivos: List[str] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    horas_totales: int = 0
    modalidad: str = "PRESENCIAL"
    area_practica: Optional[str] = None
    status: str = "DRAFT"
    calificacion_final: Optional[float] = None
    observaciones: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.objetivos is None:
            self.objetivos = []

    @property
    def duracion_dias(self) -> int:
        if self.fecha_inicio and self.fecha_fin:
            return (self.fecha_fin - self.fecha_inicio).days
        return 0

    @property
    def progreso_porcentual(self) -> float:
        if not self.fecha_inicio or not self.fecha_fin:
            return 0.0
        
        ahora = datetime.now()
        if ahora < self.fecha_inicio:
            return 0.0
        
        if ahora >= self.fecha_fin:
            return 100.0
        
        dias_transcurridos = (ahora - self.fecha_inicio).days
        dias_totales = self.duracion_dias
        
        if dias_totales == 0:
            return 0.0
        
        return (dias_transcurridos / dias_totales) * 100


@dataclass
class DocumentDTO:
    """DTO para Documento."""
    id: Optional[UUID] = None
    practice_id: Optional[UUID] = None
    tipo: str = ""
    nombre_archivo: str = ""
    ruta_archivo: str = ""
    tamaño_bytes: int = 0
    mime_type: str = ""
    subido_por: Optional[UserDTO] = None
    aprobado: bool = False
    fecha_aprobacion: Optional[datetime] = None
    aprobado_por: Optional[UserDTO] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def tamaño_legible(self) -> str:
        if self.tamaño_bytes < 1024:
            return f"{self.tamaño_bytes} B"
        elif self.tamaño_bytes < 1024 * 1024:
            return f"{self.tamaño_bytes / 1024:.1f} KB"
        else:
            return f"{self.tamaño_bytes / (1024 * 1024):.1f} MB"

    @property
    def es_imagen(self) -> bool:
        return self.mime_type.startswith('image/')

    @property
    def es_pdf(self) -> bool:
        return self.mime_type == 'application/pdf'


@dataclass
class NotificationDTO:
    """DTO para Notificación."""
    id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    titulo: str = ""
    mensaje: str = ""
    tipo: str = "INFO"
    leida: bool = False
    fecha_lectura: Optional[datetime] = None
    accion_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def es_importante(self) -> bool:
        return self.tipo in ['WARNING', 'ERROR']


@dataclass
class CreateUserRequest:
    """Request para crear usuario."""
    email: str
    first_name: str
    last_name: str
    role: str
    password: str
    is_active: bool = True


@dataclass
class CreateStudentRequest:
    """Request para crear estudiante."""
    user_data: CreateUserRequest
    codigo_estudiante: str
    documento_numero: str
    documento_tipo: str
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    carrera: Optional[str] = None
    semestre_actual: Optional[int] = None
    promedio_ponderado: Optional[float] = None


@dataclass
class CreateCompanyRequest:
    """Request para crear empresa."""
    ruc: str
    razon_social: str
    nombre_comercial: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    sector_economico: Optional[str] = None
    tamaño_empresa: Optional[str] = None


@dataclass
class CreatePracticeRequest:
    """Request para crear práctica."""
    student_id: UUID
    company_id: UUID
    titulo: str
    descripcion: str
    objetivos: List[str]
    fecha_inicio: datetime
    fecha_fin: datetime
    horas_totales: int
    modalidad: str = "PRESENCIAL"
    area_practica: Optional[str] = None


@dataclass
class UpdatePracticeRequest:
    """Request para actualizar práctica."""
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    objetivos: Optional[List[str]] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    horas_totales: Optional[int] = None
    modalidad: Optional[str] = None
    area_practica: Optional[str] = None
    observaciones: Optional[str] = None


@dataclass
class AuthenticationRequest:
    """Request para autenticación."""
    email: str
    password: str


@dataclass
class AuthenticationResponse:
    """Response de autenticación."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    user: Optional[UserDTO] = None


@dataclass
class PaginatedResponse:
    """Response paginado genérico."""
    items: List[Any]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def create(cls, items: List[Any], total: int, page: int, per_page: int):
        total_pages = (total + per_page - 1) // per_page
        return cls(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


@dataclass
class ReportRequest:
    """Request para generar reportes."""
    tipo_reporte: str
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    filtros: Optional[Dict[str, Any]] = None
    formato: str = "PDF"  # PDF, EXCEL, JSON


@dataclass
class SearchRequest:
    """Request para búsquedas."""
    query: str
    filtros: Optional[Dict[str, Any]] = None
    page: int = 1
    per_page: int = 20
    sort_by: Optional[str] = None
    sort_order: str = "ASC"  # ASC, DESC


@dataclass
class UploadDocumentRequest:
    """Request para subir documento."""
    practice_id: UUID
    tipo: str
    nombre_archivo: str
    contenido: bytes
    mime_type: str


@dataclass
class ApiResponse:
    """Response genérico de la API."""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None

    @classmethod
    def success_response(cls, data: Any = None, message: str = "Operación exitosa"):
        return cls(success=True, message=message, data=data)

    @classmethod
    def error_response(cls, message: str, errors: Optional[List[str]] = None):
        return cls(success=False, message=message, errors=errors)


@dataclass
class ValidationError:
    """Error de validación."""
    field: str
    message: str
    code: Optional[str] = None
