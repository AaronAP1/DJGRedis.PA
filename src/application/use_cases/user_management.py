"""
Casos de uso para la gestión de autenticación y usuarios.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID

from src.application.dto import (
    UserDTO, AuthenticationRequest, AuthenticationResponse, 
    CreateUserRequest, ApiResponse, ValidationError
)
from src.ports.secondary.repository_ports import (
    UserRepositoryPort, SecurityServicePort, 
    CacheServicePort, LoggingServicePort
)
from src.domain.entities import User
from src.domain.enums import UserRole
from src.domain.value_objects import Email


class AuthenticationUseCase:
    """Caso de uso para autenticación de usuarios."""

    def __init__(
        self,
        user_repository: UserRepositoryPort,
        security_service: SecurityServicePort,
        cache_service: CacheServicePort,
        logging_service: LoggingServicePort
    ):
        self.user_repository = user_repository
        self.security_service = security_service
        self.cache_service = cache_service
        self.logging_service = logging_service

    async def authenticate(self, request: AuthenticationRequest) -> ApiResponse:
        """Autentica un usuario."""
        try:
            # Validar formato de email
            try:
                email = Email(request.email)
            except ValueError as e:
                await self.logging_service.log_warning(
                    f"Intento de login con email inválido: {request.email}"
                )
                return ApiResponse.error_response("Email inválido")

            # Buscar usuario
            user = await self.user_repository.get_by_email(request.email)
            if not user:
                await self.logging_service.log_security_event(
                    "LOGIN_FAILED_USER_NOT_FOUND",
                    context={"email": request.email}
                )
                return ApiResponse.error_response("Credenciales inválidas")

            # Verificar si el usuario está activo
            if not user.is_active:
                await self.logging_service.log_security_event(
                    "LOGIN_FAILED_USER_INACTIVE",
                    user_id=user.id,
                    context={"email": request.email}
                )
                return ApiResponse.error_response("Usuario inactivo")

            # Verificar contraseña
            if not await self.security_service.verify_password(request.password, user.password_hash):
                await self.logging_service.log_security_event(
                    "LOGIN_FAILED_INVALID_PASSWORD",
                    user_id=user.id,
                    context={"email": request.email}
                )
                return ApiResponse.error_response("Credenciales inválidas")

            # Generar tokens
            access_token = await self.security_service.generate_token({
                "user_id": str(user.id),
                "email": user.email.value,
                "role": user.role.value,
                "token_type": "access"
            })

            refresh_token = await self.security_service.generate_token({
                "user_id": str(user.id),
                "token_type": "refresh"
            })

            # Actualizar último login
            user.update_last_login()
            await self.user_repository.update(user)

            # Cache user session
            await self.cache_service.set(
                f"user_session:{user.id}",
                {"user_id": str(user.id), "role": user.role.value},
                ttl=3600
            )

            # Log successful login
            await self.logging_service.log_security_event(
                "LOGIN_SUCCESS",
                user_id=user.id,
                context={"email": request.email}
            )

            # Crear response
            user_dto = self._user_to_dto(user)
            auth_response = AuthenticationResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                user=user_dto
            )

            return ApiResponse.success_response(auth_response, "Login exitoso")

        except Exception as e:
            await self.logging_service.log_error(
                f"Error en autenticación: {str(e)}",
                context={"email": request.email}
            )
            return ApiResponse.error_response("Error interno del servidor")

    async def logout(self, user_id: UUID) -> ApiResponse:
        """Cierra sesión del usuario."""
        try:
            # Eliminar sesión del cache
            await self.cache_service.delete(f"user_session:{user_id}")
            
            # Log logout
            await self.logging_service.log_security_event(
                "LOGOUT_SUCCESS",
                user_id=user_id
            )

            return ApiResponse.success_response(message="Logout exitoso")

        except Exception as e:
            await self.logging_service.log_error(
                f"Error en logout: {str(e)}",
                context={"user_id": str(user_id)}
            )
            return ApiResponse.error_response("Error al cerrar sesión")

    def _user_to_dto(self, user: User) -> UserDTO:
        """Convierte una entidad User a DTO."""
        return UserDTO(
            id=user.id,
            email=user.email.value,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role.value,
            is_active=user.is_active,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at
        )


class UserManagementUseCase:
    """Caso de uso para gestión de usuarios."""

    def __init__(
        self,
        user_repository: UserRepositoryPort,
        security_service: SecurityServicePort,
        logging_service: LoggingServicePort
    ):
        self.user_repository = user_repository
        self.security_service = security_service
        self.logging_service = logging_service

    async def create_user(self, request: CreateUserRequest, created_by: UUID) -> ApiResponse:
        """Crea un nuevo usuario."""
        try:
            # Validaciones
            validation_errors = await self._validate_create_user_request(request)
            if validation_errors:
                return ApiResponse.error_response(
                    "Errores de validación",
                    errors=[error.message for error in validation_errors]
                )

            # Verificar que el email no existe
            existing_user = await self.user_repository.get_by_email(request.email)
            if existing_user:
                return ApiResponse.error_response("El email ya está registrado")

            # Crear usuario
            email = Email(request.email)
            password_hash = await self.security_service.hash_password(request.password)
            
            user = User(
                email=email,
                first_name=request.first_name,
                last_name=request.last_name,
                role=UserRole(request.role),
                is_active=request.is_active,
                password_hash=password_hash
            )

            # Guardar usuario
            saved_user = await self.user_repository.save(user)

            # Log creation
            await self.logging_service.log_info(
                "Usuario creado",
                context={
                    "user_id": str(saved_user.id),
                    "email": request.email,
                    "role": request.role,
                    "created_by": str(created_by)
                }
            )

            user_dto = self._user_to_dto(saved_user)
            return ApiResponse.success_response(user_dto, "Usuario creado exitosamente")

        except Exception as e:
            await self.logging_service.log_error(
                f"Error creando usuario: {str(e)}",
                context={"email": request.email}
            )
            return ApiResponse.error_response("Error al crear usuario")

    async def get_user_by_id(self, user_id: UUID) -> ApiResponse:
        """Obtiene un usuario por ID."""
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return ApiResponse.error_response("Usuario no encontrado")

            user_dto = self._user_to_dto(user)
            return ApiResponse.success_response(user_dto)

        except Exception as e:
            await self.logging_service.log_error(
                f"Error obteniendo usuario: {str(e)}",
                context={"user_id": str(user_id)}
            )
            return ApiResponse.error_response("Error al obtener usuario")

    async def update_user(self, user_id: UUID, update_data: Dict[str, Any], updated_by: UUID) -> ApiResponse:
        """Actualiza un usuario."""
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return ApiResponse.error_response("Usuario no encontrado")

            # Actualizar campos permitidos
            if "first_name" in update_data:
                user.first_name = update_data["first_name"]
            if "last_name" in update_data:
                user.last_name = update_data["last_name"]
            if "is_active" in update_data:
                user.is_active = update_data["is_active"]

            # Guardar cambios
            updated_user = await self.user_repository.update(user)

            # Log update
            await self.logging_service.log_info(
                "Usuario actualizado",
                context={
                    "user_id": str(user_id),
                    "updated_fields": list(update_data.keys()),
                    "updated_by": str(updated_by)
                }
            )

            user_dto = self._user_to_dto(updated_user)
            return ApiResponse.success_response(user_dto, "Usuario actualizado exitosamente")

        except Exception as e:
            await self.logging_service.log_error(
                f"Error actualizando usuario: {str(e)}",
                context={"user_id": str(user_id)}
            )
            return ApiResponse.error_response("Error al actualizar usuario")

    async def get_users_by_role(self, role: UserRole) -> ApiResponse:
        """Obtiene usuarios por rol."""
        try:
            users = await self.user_repository.get_by_role(role)
            user_dtos = [self._user_to_dto(user) for user in users]
            return ApiResponse.success_response(user_dtos)

        except Exception as e:
            await self.logging_service.log_error(
                f"Error obteniendo usuarios por rol: {str(e)}",
                context={"role": role.value}
            )
            return ApiResponse.error_response("Error al obtener usuarios")

    async def deactivate_user(self, user_id: UUID, deactivated_by: UUID) -> ApiResponse:
        """Desactiva un usuario."""
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return ApiResponse.error_response("Usuario no encontrado")

            user.deactivate()
            await self.user_repository.update(user)

            # Log deactivation
            await self.logging_service.log_security_event(
                "USER_DEACTIVATED",
                user_id=user_id,
                context={"deactivated_by": str(deactivated_by)}
            )

            return ApiResponse.success_response(message="Usuario desactivado exitosamente")

        except Exception as e:
            await self.logging_service.log_error(
                f"Error desactivando usuario: {str(e)}",
                context={"user_id": str(user_id)}
            )
            return ApiResponse.error_response("Error al desactivar usuario")

    async def _validate_create_user_request(self, request: CreateUserRequest) -> List[ValidationError]:
        """Valida la request de creación de usuario."""
        errors = []

        # Validar email
        try:
            Email(request.email)
        except ValueError:
            errors.append(ValidationError("email", "Email inválido"))

        # Validar nombres
        if not request.first_name.strip():
            errors.append(ValidationError("first_name", "Nombre es requerido"))

        if not request.last_name.strip():
            errors.append(ValidationError("last_name", "Apellido es requerido"))

        # Validar rol
        try:
            UserRole(request.role)
        except ValueError:
            errors.append(ValidationError("role", "Rol inválido"))

        # Validar contraseña
        if len(request.password) < 8:
            errors.append(ValidationError("password", "La contraseña debe tener al menos 8 caracteres"))

        return errors

    def _user_to_dto(self, user: User) -> UserDTO:
        """Convierte una entidad User a DTO."""
        return UserDTO(
            id=user.id,
            email=user.email.value,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role.value,
            is_active=user.is_active,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
