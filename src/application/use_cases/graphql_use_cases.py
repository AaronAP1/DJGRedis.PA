"""
Casos de uso para GraphQL del sistema de gestión de prácticas profesionales.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import uuid

from src.domain.entities import User, Student, Company, Practice
from src.domain.enums import UserRole, PracticeStatus
from src.ports.secondary.repositories import (
    UserRepositoryPort, StudentRepositoryPort, CompanyRepositoryPort,
    PracticeRepositoryPort, DocumentRepositoryPort, NotificationRepositoryPort
)
from src.application.dtos import ApiResponse


@dataclass
class GraphQLRequest:
    """Base request para operaciones GraphQL."""
    user_id: str
    user_role: str


@dataclass
class CreatePracticeGraphQLRequest(GraphQLRequest):
    """Request para crear práctica vía GraphQL."""
    student_id: str
    company_id: str
    supervisor_id: Optional[str]
    titulo: str
    descripcion: str
    fecha_inicio: date
    fecha_fin: date
    horas_requeridas: int = 480


@dataclass
class UpdatePracticeStatusRequest(GraphQLRequest):
    """Request para actualizar estado de práctica."""
    practice_id: str
    new_status: str
    observations: Optional[str] = None


class GraphQLPracticeUseCase:
    """Caso de uso para operaciones GraphQL de prácticas."""
    
    def __init__(
        self,
        practice_repo: PracticeRepositoryPort,
        student_repo: StudentRepositoryPort,
        company_repo: CompanyRepositoryPort,
        notification_repo: NotificationRepositoryPort
    ):
        self.practice_repo = practice_repo
        self.student_repo = student_repo
        self.company_repo = company_repo
        self.notification_repo = notification_repo
    
    async def create_practice(self, request: CreatePracticeGraphQLRequest) -> ApiResponse:
        """Crear una nueva práctica."""
        try:
            # Validar permisos
            if request.user_role == UserRole.PRACTICANTE.value:
                # Verificar que el estudiante crea su propia práctica
                student = await self.student_repo.get_by_user_id(request.user_id)
                if not student or str(student.id) != request.student_id:
                    return ApiResponse.error_response("Solo puedes crear tu propia práctica")
            elif request.user_role not in [UserRole.COORDINADOR.value, UserRole.ADMINISTRADOR.value]:
                return ApiResponse.error_response("Sin permisos para crear prácticas")
            
            # Obtener entidades
            student = await self.student_repo.get_by_id(request.student_id)
            if not student:
                return ApiResponse.error_response("Estudiante no encontrado")
            
            company = await self.company_repo.get_by_id(request.company_id)
            if not company:
                return ApiResponse.error_response("Empresa no encontrada")
            
            # Validar elegibilidad
            if student.semestre_actual < 6:
                return ApiResponse.error_response("Estudiante debe estar en semestre 6+")
            
            if student.promedio_ponderado < 12.0:
                return ApiResponse.error_response("Promedio mínimo requerido: 12.0")
            
            # Crear práctica
            practice = Practice(
                id=str(uuid.uuid4()),
                student_id=student.id,
                company_id=company.id,
                supervisor_id=request.supervisor_id,
                titulo=request.titulo,
                descripcion=request.descripcion,
                fecha_inicio=request.fecha_inicio,
                fecha_fin=request.fecha_fin,
                horas_requeridas=request.horas_requeridas,
                status=PracticeStatus.DRAFT,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            saved_practice = await self.practice_repo.save(practice)
            
            # Crear notificación
            await self._create_notification(
                user_id=student.user_id,
                message=f"Práctica '{practice.titulo}' creada exitosamente",
                practice_id=practice.id
            )
            
            return ApiResponse.success_response(
                data=saved_practice,
                message="Práctica creada exitosamente"
            )
            
        except Exception as e:
            return ApiResponse.error_response(f"Error al crear práctica: {str(e)}")
    
    async def update_practice_status(self, request: UpdatePracticeStatusRequest) -> ApiResponse:
        """Actualizar estado de una práctica."""
        try:
            practice = await self.practice_repo.get_by_id(request.practice_id)
            if not practice:
                return ApiResponse.error_response("Práctica no encontrada")
            
            # Validar transición de estado
            validation_result = self._validate_status_transition(
                current_status=practice.status,
                new_status=request.new_status,
                user_role=request.user_role,
                practice=practice,
                user_id=request.user_id
            )
            
            if not validation_result["valid"]:
                return ApiResponse.error_response(validation_result["message"])
            
            # Actualizar estado
            practice.status = PracticeStatus(request.new_status)
            practice.updated_at = datetime.now()
            
            if request.observations:
                practice.observaciones = request.observations
            
            # Campos adicionales según estado
            if request.new_status == PracticeStatus.APPROVED.value:
                practice.fecha_aprobacion = datetime.now()
                practice.aprobado_por_id = request.user_id
            
            updated_practice = await self.practice_repo.save(practice)
            
            # Crear notificaciones relevantes
            await self._create_status_notifications(practice, request.new_status)
            
            return ApiResponse.success_response(
                data=updated_practice,
                message=f"Estado actualizado a {request.new_status}"
            )
            
        except Exception as e:
            return ApiResponse.error_response(f"Error al actualizar estado: {str(e)}")
    
    def _validate_status_transition(
        self,
        current_status: PracticeStatus,
        new_status: str,
        user_role: str,
        practice: Practice,
        user_id: str
    ) -> Dict[str, Any]:
        """Validar transición de estado según roles y reglas de negocio."""
        
        # Validaciones por estado objetivo
        if new_status == PracticeStatus.PENDING.value:
            if user_role != UserRole.PRACTICANTE.value:
                return {"valid": False, "message": "Solo el estudiante puede enviar a revisión"}
            if current_status != PracticeStatus.DRAFT:
                return {"valid": False, "message": "Solo se puede enviar desde estado DRAFT"}
        
        elif new_status in [PracticeStatus.APPROVED.value, PracticeStatus.CANCELLED.value]:
            if user_role not in [UserRole.COORDINADOR.value, UserRole.ADMINISTRADOR.value]:
                return {"valid": False, "message": "Sin permisos para aprobar/cancelar"}
            if current_status != PracticeStatus.PENDING:
                return {"valid": False, "message": "Solo se puede aprobar desde estado PENDING"}
        
        elif new_status == PracticeStatus.IN_PROGRESS.value:
            if user_role == UserRole.SUPERVISOR.value:
                # Validar que sea el supervisor asignado
                pass  # TODO: Implementar validación de supervisor
            elif user_role not in [UserRole.COORDINADOR.value, UserRole.ADMINISTRADOR.value]:
                return {"valid": False, "message": "Sin permisos"}
            if current_status != PracticeStatus.APPROVED:
                return {"valid": False, "message": "Solo se puede iniciar desde estado APPROVED"}
        
        elif new_status == PracticeStatus.COMPLETED.value:
            if user_role not in [UserRole.SUPERVISOR.value, UserRole.COORDINADOR.value, UserRole.ADMINISTRADOR.value]:
                return {"valid": False, "message": "Sin permisos para completar"}
            if current_status != PracticeStatus.IN_PROGRESS:
                return {"valid": False, "message": "Solo se puede completar desde estado IN_PROGRESS"}
        
        return {"valid": True, "message": "Transición válida"}
    
    async def _create_notification(
        self,
        user_id: str,
        message: str,
        practice_id: Optional[str] = None
    ):
        """Crear notificación para un usuario."""
        try:
            # TODO: Implementar creación de notificación
            pass
        except Exception:
            # Log error but don't fail the main operation
            pass
    
    async def _create_status_notifications(self, practice: Practice, new_status: str):
        """Crear notificaciones relevantes cuando cambia el estado."""
        try:
            if new_status == PracticeStatus.APPROVED.value:
                await self._create_notification(
                    user_id=practice.student_id,
                    message=f"Tu práctica '{practice.titulo}' ha sido aprobada",
                    practice_id=practice.id
                )
            
            elif new_status == PracticeStatus.IN_PROGRESS.value:
                await self._create_notification(
                    user_id=practice.student_id,
                    message=f"Tu práctica '{practice.titulo}' ha iniciado",
                    practice_id=practice.id
                )
            
            elif new_status == PracticeStatus.COMPLETED.value:
                await self._create_notification(
                    user_id=practice.student_id,
                    message=f"¡Felicitaciones! Has completado la práctica '{practice.titulo}'",
                    practice_id=practice.id
                )
        except Exception:
            # Log error but don't fail the main operation
            pass


@dataclass
class CreateUserGraphQLRequest(GraphQLRequest):
    """Request para crear usuario vía GraphQL."""
    email: str
    password: str
    first_name: str
    last_name: str
    role: str


class GraphQLUserUseCase:
    """Caso de uso para operaciones GraphQL de usuarios."""
    
    def __init__(
        self,
        user_repo: UserRepositoryPort,
        notification_repo: NotificationRepositoryPort
    ):
        self.user_repo = user_repo
        self.notification_repo = notification_repo
    
    async def create_user(self, request: CreateUserGraphQLRequest) -> ApiResponse:
        """Crear un nuevo usuario."""
        try:
            # Validar permisos
            if request.user_role not in [UserRole.COORDINADOR.value, UserRole.ADMINISTRADOR.value]:
                return ApiResponse.error_response("Sin permisos para crear usuarios")
            
            # Validar que el email no exista
            existing_user = await self.user_repo.get_by_email(request.email)
            if existing_user:
                return ApiResponse.error_response("Email ya registrado")
            
            # Crear usuario
            user = User(
                id=str(uuid.uuid4()),
                email=request.email,
                first_name=request.first_name,
                last_name=request.last_name,
                role=UserRole(request.role),
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Asignar password (será hasheado por el repositorio)
            user.password = request.password
            
            saved_user = await self.user_repo.save(user)
            
            # Crear notificación de bienvenida
            await self._create_notification(
                user_id=saved_user.id,
                message=f"Bienvenido al sistema de gestión de prácticas profesionales"
            )
            
            return ApiResponse.success_response(
                data=saved_user,
                message="Usuario creado exitosamente"
            )
            
        except Exception as e:
            return ApiResponse.error_response(f"Error al crear usuario: {str(e)}")
    
    async def _create_notification(self, user_id: str, message: str):
        """Crear notificación para un usuario."""
        try:
            # TODO: Implementar creación de notificación
            pass
        except Exception:
            pass
