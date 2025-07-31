"""
Entidades del dominio de gestión de prácticas profesionales.
Las entidades tienen identidad y pueden cambiar su estado a lo largo del tiempo.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from .enums import UserRole, PracticeStatus, CompanyStatus, DocumentType
from .value_objects import (
    Email, Documento, Telefono, Direccion, Periodo, 
    Calificacion, CodigoEstudiante, RUC
)


@dataclass
class Entity(ABC):
    """Clase base para todas las entidades del dominio."""
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


@dataclass
class User(Entity):
    """Entidad Usuario del sistema."""
    email: Email = field(default=None)
    first_name: str = ""
    last_name: str = ""
    role: UserRole = UserRole.PRACTICANTE
    is_active: bool = True
    last_login: Optional[datetime] = None
    password_hash: Optional[str] = None

    def full_name(self) -> str:
        """Retorna el nombre completo del usuario."""
        return f"{self.first_name} {self.last_name}"

    def can_perform_action(self, action: str) -> bool:
        """Verifica si el usuario puede realizar una acción específica."""
        permissions = UserRole.get_permissions(self.role)
        return action in permissions or 'full_system_access' in permissions

    def update_last_login(self):
        """Actualiza la fecha del último login."""
        self.last_login = datetime.now()
        self.updated_at = datetime.now()

    def deactivate(self):
        """Desactiva el usuario."""
        self.is_active = False
        self.updated_at = datetime.now()

    def activate(self):
        """Activa el usuario."""
        self.is_active = True
        self.updated_at = datetime.now()


@dataclass
class Student(Entity):
    """Entidad Estudiante (Practicante)."""
    user: User
    codigo_estudiante: CodigoEstudiante
    documento: Documento
    telefono: Optional[Telefono] = None
    direccion: Optional[Direccion] = None
    carrera: Optional[str] = None
    semestre_actual: Optional[int] = None
    promedio_ponderado: Optional[float] = None

    def __post_init__(self):
        if self.user.role != UserRole.PRACTICANTE:
            raise ValueError("El usuario debe tener rol PRACTICANTE")

    def puede_realizar_practica(self) -> bool:
        """Verifica si el estudiante puede realizar una práctica."""
        # Reglas de negocio: mínimo en 6to semestre y promedio >= 12
        return (self.semestre_actual is not None and 
                self.semestre_actual >= 6 and
                self.promedio_ponderado is not None and 
                self.promedio_ponderado >= 12.0)

    def actualizar_datos_academicos(self, semestre: int, promedio: float):
        """Actualiza los datos académicos del estudiante."""
        self.semestre_actual = semestre
        self.promedio_ponderado = promedio
        self.updated_at = datetime.now()


@dataclass
class Company(Entity):
    """Entidad Empresa."""
    ruc: RUC
    razon_social: str
    nombre_comercial: Optional[str] = None
    direccion: Optional[Direccion] = None
    telefono: Optional[Telefono] = None
    email: Optional[Email] = None
    sector_economico: Optional[str] = None
    tamaño_empresa: Optional[str] = None  # MICRO, PEQUEÑA, MEDIANA, GRANDE
    status: CompanyStatus = CompanyStatus.PENDING_VALIDATION
    fecha_validacion: Optional[datetime] = None

    def validar_empresa(self):
        """Marca la empresa como validada."""
        self.status = CompanyStatus.ACTIVE
        self.fecha_validacion = datetime.now()
        self.updated_at = datetime.now()

    def suspender_empresa(self, motivo: str):
        """Suspende la empresa."""
        self.status = CompanyStatus.SUSPENDED
        self.updated_at = datetime.now()
        # Aquí se podría agregar un log del motivo

    def puede_recibir_practicantes(self) -> bool:
        """Verifica si la empresa puede recibir practicantes."""
        return self.status == CompanyStatus.ACTIVE

    def nombre_para_mostrar(self) -> str:
        """Retorna el nombre comercial o razón social."""
        return self.nombre_comercial or self.razon_social


@dataclass
class Supervisor(Entity):
    """Entidad Supervisor de empresa."""
    user: User
    company: Company
    documento: Documento
    cargo: str
    telefono: Optional[Telefono] = None
    años_experiencia: Optional[int] = None

    def __post_init__(self):
        if self.user.role != UserRole.SUPERVISOR:
            raise ValueError("El usuario debe tener rol SUPERVISOR")

    def puede_supervisar_practica(self, practice: 'Practice') -> bool:
        """Verifica si puede supervisar una práctica específica."""
        return (self.company.id == practice.company.id and 
                self.company.puede_recibir_practicantes())


@dataclass
class Practice(Entity):
    """Entidad Práctica Profesional."""
    student: Student
    company: Company
    supervisor: Optional[Supervisor] = None
    titulo: str = ""
    descripcion: str = ""
    objetivos: List[str] = field(default_factory=list)
    periodo: Optional[Periodo] = None
    horas_totales: int = 0
    modalidad: str = "PRESENCIAL"  # PRESENCIAL, REMOTO, HIBRIDO
    area_practica: Optional[str] = None
    status: PracticeStatus = PracticeStatus.DRAFT
    calificacion_final: Optional[Calificacion] = None
    observaciones: str = ""

    def asignar_supervisor(self, supervisor: Supervisor):
        """Asigna un supervisor a la práctica."""
        if not supervisor.puede_supervisar_practica(self):
            raise ValueError("El supervisor no puede supervisar esta práctica")
        
        self.supervisor = supervisor
        self.updated_at = datetime.now()

    def aprobar_practica(self):
        """Aprueba la práctica para iniciar."""
        if self.status != PracticeStatus.PENDING:
            raise ValueError("Solo se pueden aprobar prácticas pendientes")
        
        if not self.supervisor:
            raise ValueError("La práctica debe tener un supervisor asignado")
        
        self.status = PracticeStatus.APPROVED
        self.updated_at = datetime.now()

    def iniciar_practica(self):
        """Inicia la práctica."""
        if self.status != PracticeStatus.APPROVED:
            raise ValueError("Solo se pueden iniciar prácticas aprobadas")
        
        self.status = PracticeStatus.IN_PROGRESS
        self.updated_at = datetime.now()

    def finalizar_practica(self, calificacion: Calificacion, observaciones: str = ""):
        """Finaliza la práctica con calificación."""
        if self.status != PracticeStatus.IN_PROGRESS:
            raise ValueError("Solo se pueden finalizar prácticas en progreso")
        
        self.calificacion_final = calificacion
        self.observaciones = observaciones
        self.status = PracticeStatus.COMPLETED
        self.updated_at = datetime.now()

    def cancelar_practica(self, motivo: str):
        """Cancela la práctica."""
        if self.status in [PracticeStatus.COMPLETED, PracticeStatus.CANCELLED]:
            raise ValueError("No se puede cancelar una práctica finalizada o ya cancelada")
        
        self.status = PracticeStatus.CANCELLED
        self.observaciones = motivo
        self.updated_at = datetime.now()

    def esta_activa(self) -> bool:
        """Verifica si la práctica está activa."""
        return self.status == PracticeStatus.IN_PROGRESS

    def puede_ser_evaluada(self) -> bool:
        """Verifica si la práctica puede ser evaluada."""
        return self.status == PracticeStatus.IN_PROGRESS

    def duracion_completada(self) -> int:
        """Retorna los días completados de práctica."""
        if not self.periodo or self.status != PracticeStatus.IN_PROGRESS:
            return 0
        
        ahora = datetime.now()
        if ahora < self.periodo.fecha_inicio:
            return 0
        
        fecha_limite = min(ahora, self.periodo.fecha_fin)
        return (fecha_limite - self.periodo.fecha_inicio).days

    def progreso_porcentual(self) -> float:
        """Retorna el progreso de la práctica en porcentaje."""
        if not self.periodo:
            return 0.0
        
        dias_completados = self.duracion_completada()
        dias_totales = self.periodo.duracion_dias()
        
        if dias_totales == 0:
            return 0.0
        
        return min(100.0, (dias_completados / dias_totales) * 100)


@dataclass
class Document(Entity):
    """Entidad Documento."""
    practice: Practice
    tipo: DocumentType
    nombre_archivo: str
    ruta_archivo: str
    tamaño_bytes: int
    mime_type: str
    subido_por: User
    aprobado: bool = False
    fecha_aprobacion: Optional[datetime] = None
    aprobado_por: Optional[User] = None

    def aprobar_documento(self, aprobado_por: User):
        """Aprueba el documento."""
        self.aprobado = True
        self.fecha_aprobacion = datetime.now()
        self.aprobado_por = aprobado_por
        self.updated_at = datetime.now()

    def rechazar_documento(self):
        """Rechaza el documento."""
        self.aprobado = False
        self.fecha_aprobacion = None
        self.aprobado_por = None
        self.updated_at = datetime.now()

    def es_imagen(self) -> bool:
        """Verifica si el documento es una imagen."""
        return self.mime_type.startswith('image/')

    def es_pdf(self) -> bool:
        """Verifica si el documento es un PDF."""
        return self.mime_type == 'application/pdf'

    def tamaño_legible(self) -> str:
        """Retorna el tamaño del archivo en formato legible."""
        if self.tamaño_bytes < 1024:
            return f"{self.tamaño_bytes} B"
        elif self.tamaño_bytes < 1024 * 1024:
            return f"{self.tamaño_bytes / 1024:.1f} KB"
        else:
            return f"{self.tamaño_bytes / (1024 * 1024):.1f} MB"


@dataclass
class Notification(Entity):
    """Entidad Notificación."""
    user: User
    titulo: str
    mensaje: str
    tipo: str  # INFO, WARNING, ERROR, SUCCESS
    leida: bool = False
    fecha_lectura: Optional[datetime] = None
    accion_url: Optional[str] = None

    def marcar_como_leida(self):
        """Marca la notificación como leída."""
        self.leida = True
        self.fecha_lectura = datetime.now()
        self.updated_at = datetime.now()

    def es_importante(self) -> bool:
        """Verifica si la notificación es importante."""
        return self.tipo in ['WARNING', 'ERROR']
