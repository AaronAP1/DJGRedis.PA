<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Instrucciones para GitHub Copilot

## Contexto del Proyecto
Este es un sistema de gestión de prácticas profesionales desarrollado como proyecto de graduación en Ingeniería de Sistemas. El proyecto utiliza **Arquitectura Hexagonal (Ports and Adapters)** con Django.

## Arquitectura
- **Dominio**: Entidades, value objects y reglas de negocio puras
- **Puertos**: Interfaces que definen contratos
- **Adaptadores**: Implementaciones concretas (Django, Redis, PostgreSQL)
- **Aplicación**: Casos de uso y DTOs

## Roles del Sistema
- **PRACTICANTE**: Estudiantes realizando prácticas
- **SUPERVISOR**: Supervisores de empresas  
- **COORDINADOR**: Coordinadores académicos
- **SECRETARIA**: Personal administrativo
- **ADMINISTRADOR**: Administradores del sistema

## Tecnologías Principales
- Django 5.0+ con DRF
- PostgreSQL + Redis + MongoDB
- Celery para tareas asíncronas
- JWT para autenticación
- Docker para contenedores
- Pytest para testing

## Convenciones de Código

### Naming
- Clases: PascalCase
- Funciones/métodos: snake_case
- Constantes: UPPER_SNAKE_CASE
- Archivos: snake_case.py

### Estructura de Archivos
```
src/
├── domain/           # Lógica de negocio pura
├── ports/           # Interfaces
├── adapters/        # Implementaciones
└── application/     # Casos de uso
```

### Testing
- Tests unitarios para dominio
- Tests de integración para adaptadores
- Mocks para dependencias externas
- Cobertura mínima: 80%

### Security
- Siempre validar inputs
- Usar logging de seguridad para eventos críticos
- Implementar rate limiting
- Encriptar datos sensibles

## Patrones a Seguir

### Repository Pattern
```python
class UserRepositoryPort(ABC):
    @abstractmethod
    async def save(self, user: User) -> User:
        pass
```

### Use Case Pattern
```python
class CreateUserUseCase:
    def __init__(self, user_repo: UserRepositoryPort):
        self.user_repo = user_repo
    
    async def execute(self, request: CreateUserRequest) -> ApiResponse:
        # Validaciones
        # Lógica de negocio
        # Persistencia
        pass
```

### DTO Pattern
```python
@dataclass
class UserDTO:
    id: UUID
    email: str
    role: str
```

## Reglas de Negocio Importantes

### Estudiantes
- Deben estar en semestre 6+ para prácticas
- Promedio mínimo 12.0
- Código formato: YYYY + 6 dígitos

### Empresas
- RUC válido de 11 dígitos
- Estado ACTIVE para recibir practicantes
- Validación obligatoria

### Prácticas
- Duración mínima 480 horas
- Supervisor asignado obligatorio
- Estados: DRAFT → PENDING → APPROVED → IN_PROGRESS → COMPLETED

## Error Handling
```python
try:
    # Operación
    pass
except DomainException as e:
    return ApiResponse.error_response(str(e))
except Exception as e:
    await logging_service.log_error(str(e))
    return ApiResponse.error_response("Error interno")
```

## Logging
```python
await logging_service.log_security_event(
    "LOGIN_SUCCESS",
    user_id=user.id,
    context={"email": email}
)
```

## Performance
- Usar async/await para I/O
- Cache en Redis para consultas frecuentes
- Paginación para listas grandes
- Índices en campos de búsqueda

## Cuando generes código:
1. Respeta la arquitectura hexagonal
2. Implementa validaciones apropiadas
3. Incluye logging de seguridad
4. Usa tipos hint
5. Agrega docstrings
6. Maneja errores correctamente
7. Considera performance
8. Escribe tests correspondientes
