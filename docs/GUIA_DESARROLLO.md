# 💻 Guía de Desarrollo - Sistema de Gestión de Prácticas Profesionales

## 📋 Tabla de Contenidos

- [Arquitectura del Proyecto](#arquitectura-del-proyecto)
- [Estructura de Directorios](#estructura-de-directorios)
- [Convenciones de Código](#convenciones-de-código)
- [Patrones de Diseño](#patrones-de-diseño)
- [Desarrollo de Nuevas Features](#desarrollo-de-nuevas-features)
- [Testing](#testing)
- [Git Workflow](#git-workflow)
- [Performance y Optimización](#performance-y-optimización)

---

## 🏗️ Arquitectura del Proyecto

El proyecto utiliza **Arquitectura Hexagonal (Ports and Adapters)** para mantener la lógica de negocio independiente de las implementaciones técnicas.

### Capas de la Arquitectura

```
┌─────────────────────────────────────────────┐
│           ADAPTERS (Primary)                │
│   REST API, GraphQL, CLI, WebSockets        │
├─────────────────────────────────────────────┤
│            PORTS (Primary)                  │
│         Interfaces de Entrada               │
├─────────────────────────────────────────────┤
│         APPLICATION LAYER                   │
│   Use Cases, DTOs, Application Services    │
├─────────────────────────────────────────────┤
│           DOMAIN LAYER                      │
│  Entities, Value Objects, Domain Logic     │
├─────────────────────────────────────────────┤
│           PORTS (Secondary)                 │
│         Interfaces de Salida                │
├─────────────────────────────────────────────┤
│          ADAPTERS (Secondary)               │
│   Database, Redis, Email, External APIs    │
└─────────────────────────────────────────────┘
```

### Principios Fundamentales

1. **Dependency Inversion**: El dominio no depende de infraestructura
2. **Separation of Concerns**: Cada capa tiene responsabilidad única
3. **Testability**: Lógica de negocio fácilmente testeable
4. **Flexibility**: Cambiar implementaciones sin afectar el dominio

---

## 📂 Estructura de Directorios

```
DJGRedis.PA/
├── config/                    # Configuración Django
│   ├── settings.py           # Settings principales
│   ├── urls.py               # URLs principales
│   ├── celery.py             # Configuración Celery
│   └── wsgi.py / asgi.py     # WSGI/ASGI
│
├── src/                       # Código fuente principal
│   ├── domain/               # ⭐ Capa de Dominio
│   │   ├── entities.py       # Entidades del negocio
│   │   ├── value_objects.py  # Value Objects
│   │   ├── enums.py          # Enumeraciones
│   │   └── models.py         # Modelos Django (implementación)
│   │
│   ├── application/          # ⭐ Capa de Aplicación
│   │   ├── dto.py            # Data Transfer Objects
│   │   └── use_cases/        # Casos de Uso
│   │       ├── users/
│   │       ├── practices/
│   │       └── ...
│   │
│   ├── ports/                # ⭐ Puertos (Interfaces)
│   │   ├── primary/          # Entrada (REST, GraphQL)
│   │   └── secondary/        # Salida (Repos, Services)
│   │
│   ├── adapters/             # ⭐ Adaptadores
│   │   ├── primary/          # Entrada
│   │   │   ├── rest_api/    # REST API ViewSets
│   │   │   └── graphql_api/ # GraphQL Queries/Mutations
│   │   └── secondary/        # Salida
│   │       ├── repositories/ # Repositorios Django ORM
│   │       ├── email/        # Servicio de Email
│   │       └── cache/        # Cache Redis
│   │
│   └── infrastructure/       # ⭐ Infraestructura
│       ├── middleware/       # Middleware personalizado
│       ├── security/         # Permisos, Auth, JWT
│       └── logging/          # Logging y auditoría
│
├── tests/                    # Tests
│   ├── unit/                 # Tests unitarios
│   ├── integration/          # Tests de integración
│   └── e2e/                  # Tests end-to-end
│
├── docs/                     # Documentación
├── scripts/                  # Scripts útiles
├── requirements/             # Dependencias
├── templates/                # Templates HTML
├── logs/                     # Archivos de log
└── backups/                  # Backups
```

---

## 📝 Convenciones de Código

### Naming Conventions

```python
# Clases: PascalCase
class UserRepository:
    pass

class PracticeValidationService:
    pass

# Funciones y métodos: snake_case
def calculate_total_hours():
    pass

def send_notification_email():
    pass

# Constantes: UPPER_SNAKE_CASE
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB
DEFAULT_PRACTICE_HOURS = 480

# Variables: snake_case
user_email = "test@upeu.edu.pe"
practice_status = "IN_PROGRESS"

# Archivos y módulos: snake_case
user_repository.py
practice_use_cases.py
```

### Type Hints

**Siempre usa type hints**:

```python
from typing import Optional, List, Dict
from decimal import Decimal
from datetime import datetime

def create_practice(
    student_id: int,
    company_id: int,
    start_date: datetime,
    expected_hours: int = 480
) -> Practice:
    """Crea una nueva práctica profesional."""
    pass

def get_practices_by_status(
    status: str,
    limit: Optional[int] = None
) -> List[Practice]:
    """Obtiene prácticas filtradas por estado."""
    pass

async def calculate_average_grade(
    practice_id: int
) -> Optional[Decimal]:
    """Calcula el promedio de calificaciones."""
    pass
```

### Docstrings

Usa formato **Google Style**:

```python
def validate_practice_requirements(student: Student, practice: Practice) -> bool:
    """
    Valida que el estudiante cumpla los requisitos para la práctica.
    
    Args:
        student: Instancia del estudiante a validar
        practice: Instancia de la práctica solicitada
        
    Returns:
        True si cumple todos los requisitos, False en caso contrario
        
    Raises:
        ValidationError: Si los datos son inválidos
        
    Examples:
        >>> student = Student.objects.get(id=1)
        >>> practice = Practice.objects.get(id=5)
        >>> validate_practice_requirements(student, practice)
        True
    """
    if student.semestre_actual < 6:
        return False
    if student.promedio_ponderado < Decimal('12.0'):
        return False
    return True
```

### Imports

Orden de imports:

```python
# 1. Standard library
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, List

# 2. Third-party
import django
from django.db import models
from rest_framework import viewsets
from graphene import ObjectType

# 3. Local application
from src.domain.entities import Practice
from src.domain.enums import UserRole
from src.application.dto import PracticeDTO
from src.infrastructure.security.permissions import IsCoordinador
```

---

## 🎨 Patrones de Diseño

### 1. Repository Pattern

**Definir Puerto (Interface)**:

```python
# src/ports/secondary/repositories.py
from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.entities import Practice

class PracticeRepositoryPort(ABC):
    """Puerto para repositorio de prácticas."""
    
    @abstractmethod
    def save(self, practice: Practice) -> Practice:
        """Guarda una práctica."""
        pass
    
    @abstractmethod
    def find_by_id(self, practice_id: int) -> Optional[Practice]:
        """Busca una práctica por ID."""
        pass
    
    @abstractmethod
    def find_by_student(self, student_id: int) -> List[Practice]:
        """Busca prácticas por estudiante."""
        pass
    
    @abstractmethod
    def delete(self, practice_id: int) -> bool:
        """Elimina una práctica."""
        pass
```

**Implementar Adaptador**:

```python
# src/adapters/secondary/repositories/practice_repository.py
from src.ports.secondary.repositories import PracticeRepositoryPort
from src.domain.models import Practice

class DjangoPracticeRepository(PracticeRepositoryPort):
    """Implementación Django ORM del repositorio de prácticas."""
    
    def save(self, practice: Practice) -> Practice:
        practice.save()
        return practice
    
    def find_by_id(self, practice_id: int) -> Optional[Practice]:
        try:
            return Practice.objects.select_related(
                'student__user',
                'company',
                'supervisor__user'
            ).get(id=practice_id)
        except Practice.DoesNotExist:
            return None
    
    def find_by_student(self, student_id: int) -> List[Practice]:
        return list(
            Practice.objects.filter(student_id=student_id)
            .select_related('company', 'supervisor')
            .order_by('-fecha_inicio')
        )
    
    def delete(self, practice_id: int) -> bool:
        try:
            Practice.objects.get(id=practice_id).delete()
            return True
        except Practice.DoesNotExist:
            return False
```

### 2. Use Case Pattern

```python
# src/application/use_cases/practices/create_practice.py
from dataclasses import dataclass
from datetime import datetime
from src.ports.secondary.repositories import (
    PracticeRepositoryPort,
    StudentRepositoryPort,
    CompanyRepositoryPort
)
from src.domain.models import Practice
from src.domain.enums import PracticeStatus

@dataclass
class CreatePracticeRequest:
    """Request DTO para crear práctica."""
    student_id: int
    company_id: int
    area: str
    start_date: datetime
    expected_hours: int = 480

class CreatePracticeUseCase:
    """Caso de uso: Crear nueva práctica."""
    
    def __init__(
        self,
        practice_repo: PracticeRepositoryPort,
        student_repo: StudentRepositoryPort,
        company_repo: CompanyRepositoryPort
    ):
        self.practice_repo = practice_repo
        self.student_repo = student_repo
        self.company_repo = company_repo
    
    def execute(self, request: CreatePracticeRequest) -> Practice:
        """
        Ejecuta el caso de uso de crear práctica.
        
        Args:
            request: Datos de la solicitud
            
        Returns:
            Práctica creada
            
        Raises:
            ValidationError: Si los datos no son válidos
            NotFoundException: Si estudiante o empresa no existen
        """
        # 1. Validar que el estudiante existe
        student = self.student_repo.find_by_id(request.student_id)
        if not student:
            raise NotFoundException(f"Estudiante {request.student_id} no encontrado")
        
        # 2. Validar requisitos académicos
        if student.semestre_actual < 6:
            raise ValidationError("El estudiante debe estar en semestre 6 o superior")
        
        if student.promedio_ponderado < 12.0:
            raise ValidationError("El promedio debe ser mayor o igual a 12.0")
        
        # 3. Validar que la empresa existe y está activa
        company = self.company_repo.find_by_id(request.company_id)
        if not company:
            raise NotFoundException(f"Empresa {request.company_id} no encontrada")
        
        if not company.validated or company.estado != 'ACTIVE':
            raise ValidationError("La empresa debe estar validada y activa")
        
        # 4. Crear la práctica
        practice = Practice(
            student=student,
            company=company,
            area=request.area,
            fecha_inicio=request.start_date,
            horas_requeridas=request.expected_hours,
            estado=PracticeStatus.DRAFT.value
        )
        
        # 5. Guardar
        saved_practice = self.practice_repo.save(practice)
        
        # 6. Enviar notificación (opcional)
        # self.notification_service.notify_new_practice(saved_practice)
        
        return saved_practice
```

**Usar en ViewSet**:

```python
# src/adapters/primary/rest_api/views/practices.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from src.application.use_cases.practices.create_practice import (
    CreatePracticeUseCase,
    CreatePracticeRequest
)
from src.adapters.secondary.repositories.practice_repository import DjangoPracticeRepository
from src.adapters.secondary.repositories.student_repository import DjangoStudentRepository
from src.adapters.secondary.repositories.company_repository import DjangoCompanyRepository

class PracticeViewSet(viewsets.ViewSet):
    """ViewSet para gestión de prácticas."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Inyección de dependencias
        self.create_practice_use_case = CreatePracticeUseCase(
            practice_repo=DjangoPracticeRepository(),
            student_repo=DjangoStudentRepository(),
            company_repo=DjangoCompanyRepository()
        )
    
    @action(detail=False, methods=['post'])
    def create(self, request):
        """Crea una nueva práctica."""
        try:
            # Crear request DTO
            use_case_request = CreatePracticeRequest(
                student_id=request.data['student_id'],
                company_id=request.data['company_id'],
                area=request.data['area'],
                start_date=request.data['start_date'],
                expected_hours=request.data.get('expected_hours', 480)
            )
            
            # Ejecutar caso de uso
            practice = self.create_practice_use_case.execute(use_case_request)
            
            # Serializar respuesta
            serializer = PracticeSerializer(practice)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except NotFoundException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
```

### 3. DTO Pattern

```python
# src/application/dto.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal

@dataclass
class UserDTO:
    """DTO para transferencia de datos de usuario."""
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    created_at: datetime

@dataclass
class PracticeDTO:
    """DTO para transferencia de datos de práctica."""
    id: int
    student: UserDTO
    company_name: str
    area: str
    start_date: datetime
    end_date: Optional[datetime]
    total_hours: int
    required_hours: int
    status: str
    average_grade: Optional[Decimal]
    
    @property
    def progress_percentage(self) -> float:
        """Calcula el porcentaje de avance."""
        if self.required_hours == 0:
            return 0.0
        return (self.total_hours / self.required_hours) * 100
```

---

## 🚀 Desarrollo de Nuevas Features

### Checklist para Nueva Feature

- [ ] 1. Definir requisitos y casos de uso
- [ ] 2. Crear/actualizar entidades de dominio
- [ ] 3. Definir puertos (interfaces)
- [ ] 4. Implementar casos de uso (application layer)
- [ ] 5. Implementar adaptadores (REST, GraphQL, repos)
- [ ] 6. Agregar permisos y validaciones
- [ ] 7. Escribir tests (unit, integration)
- [ ] 8. Actualizar documentación
- [ ] 9. Code review
- [ ] 10. Deploy

### Ejemplo: Agregar Sistema de Comentarios

#### 1. Entidad de Dominio

```python
# src/domain/models.py
class Comment(models.Model):
    """Comentarios en prácticas."""
    
    practice = models.ForeignKey(
        'Practice',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        'User',
        on_delete=models.CASCADE
    )
    content = models.TextField()
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['practice', '-created_at']),
        ]
```

#### 2. Puerto (Interface)

```python
# src/ports/secondary/repositories.py
class CommentRepositoryPort(ABC):
    @abstractmethod
    def save(self, comment: Comment) -> Comment:
        pass
    
    @abstractmethod
    def find_by_practice(
        self,
        practice_id: int,
        include_private: bool = False
    ) -> List[Comment]:
        pass
```

#### 3. Caso de Uso

```python
# src/application/use_cases/comments/add_comment.py
@dataclass
class AddCommentRequest:
    practice_id: int
    author_id: int
    content: str
    is_private: bool = False

class AddCommentUseCase:
    def __init__(
        self,
        comment_repo: CommentRepositoryPort,
        practice_repo: PracticeRepositoryPort
    ):
        self.comment_repo = comment_repo
        self.practice_repo = practice_repo
    
    def execute(self, request: AddCommentRequest) -> Comment:
        # Validar que la práctica existe
        practice = self.practice_repo.find_by_id(request.practice_id)
        if not practice:
            raise NotFoundException("Práctica no encontrada")
        
        # Crear comentario
        comment = Comment(
            practice_id=request.practice_id,
            author_id=request.author_id,
            content=request.content,
            is_private=request.is_private
        )
        
        # Guardar
        return self.comment_repo.save(comment)
```

#### 4. Serializer

```python
# src/adapters/primary/rest_api/serializers.py
class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(
        source='author.get_full_name',
        read_only=True
    )
    
    class Meta:
        model = Comment
        fields = [
            'id',
            'practice',
            'author',
            'author_name',
            'content',
            'is_private',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
```

#### 5. ViewSet

```python
# src/adapters/primary/rest_api/views/comments.py
class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        practice_id = self.request.query_params.get('practice_id')
        if not practice_id:
            return Comment.objects.none()
        
        queryset = Comment.objects.filter(practice_id=practice_id)
        
        # Solo mostrar privados si es coordinador/supervisor
        if not self.request.user.is_coordinador_or_supervisor:
            queryset = queryset.filter(is_private=False)
        
        return queryset.select_related('author', 'practice')
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
```

#### 6. URLs

```python
# src/adapters/primary/rest_api/urls_api_v2.py
router.register(r'comments', CommentViewSet, basename='comment')
```

#### 7. Tests

```python
# tests/unit/test_comments.py
import pytest
from src.application.use_cases.comments.add_comment import (
    AddCommentUseCase,
    AddCommentRequest
)

class TestAddCommentUseCase:
    def test_add_comment_success(self, mock_repos):
        # Arrange
        use_case = AddCommentUseCase(
            comment_repo=mock_repos['comment'],
            practice_repo=mock_repos['practice']
        )
        request = AddCommentRequest(
            practice_id=1,
            author_id=1,
            content="Test comment"
        )
        
        # Act
        comment = use_case.execute(request)
        
        # Assert
        assert comment.content == "Test comment"
        assert comment.practice_id == 1
```

---

## 🧪 Testing

### Estructura de Tests

```
tests/
├── unit/                     # Tests unitarios (lógica de negocio)
│   ├── test_use_cases.py
│   ├── test_entities.py
│   └── test_value_objects.py
│
├── integration/              # Tests de integración (con DB)
│   ├── test_repositories.py
│   ├── test_viewsets.py
│   └── test_serializers.py
│
└── e2e/                      # Tests end-to-end
    ├── test_practice_flow.py
    └── test_auth_flows.py
```

### Tests Unitarios

```python
# tests/unit/test_use_cases.py
import pytest
from unittest.mock import Mock
from src.application.use_cases.practices.create_practice import CreatePracticeUseCase

@pytest.fixture
def mock_repositories():
    """Fixture con repositorios mockeados."""
    return {
        'practice': Mock(),
        'student': Mock(),
        'company': Mock()
    }

def test_create_practice_success(mock_repositories):
    """Test: Crear práctica con datos válidos."""
    # Arrange
    use_case = CreatePracticeUseCase(**mock_repositories)
    
    # Configurar mocks
    mock_student = Mock(semestre_actual=7, promedio_ponderado=15.0)
    mock_company = Mock(validated=True, estado='ACTIVE')
    
    mock_repositories['student'].find_by_id.return_value = mock_student
    mock_repositories['company'].find_by_id.return_value = mock_company
    
    # Act
    result = use_case.execute(request)
    
    # Assert
    assert result is not None
    mock_repositories['practice'].save.assert_called_once()
```

### Tests de Integración

```python
# tests/integration/test_viewsets.py
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from src.domain.models import User, Student, Company, Practice

class PracticeViewSetTest(TestCase):
    """Tests de integración para PracticeViewSet."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.client = APIClient()
        
        # Crear usuario coordinador
        self.coordinator = User.objects.create_user(
            email='coordinator@upeu.edu.pe',
            password='test123',
            role='COORDINADOR'
        )
        
        # Crear estudiante
        self.student_user = User.objects.create_user(
            email='student@upeu.edu.pe',
            password='test123',
            role='PRACTICANTE'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            codigo_estudiante='2024012345',
            semestre_actual=7,
            promedio_ponderado=15.0
        )
        
        # Crear empresa
        self.company = Company.objects.create(
            razon_social='Test Corp',
            ruc='20123456789',
            validated=True,
            estado='ACTIVE'
        )
    
    def test_list_practices_as_coordinator(self):
        """Test: Listar prácticas como coordinador."""
        # Autenticar
        self.client.force_authenticate(user=self.coordinator)
        
        # Crear práctica
        Practice.objects.create(
            student=self.student,
            company=self.company,
            area='Desarrollo Web',
            estado='IN_PROGRESS'
        )
        
        # Hacer request
        response = self.client.get('/api/v2/practices/')
        
        # Assertions
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['area'] == 'Desarrollo Web'
    
    def test_create_practice_unauthorized(self):
        """Test: Crear práctica sin autenticación."""
        response = self.client.post('/api/v2/practices/', {})
        assert response.status_code == 401
```

### Ejecutar Tests

```bash
# Todos los tests
python manage.py test

# Tests específicos
python manage.py test tests.unit.test_use_cases

# Con pytest
pytest

# Con cobertura
pytest --cov=src --cov-report=html
firefox htmlcov/index.html

# Tests en paralelo
pytest -n auto
```

---

## 🔀 Git Workflow

### Branching Strategy

```
master (production)
  └─ develop
      ├─ feature/add-comments
      ├─ feature/improve-dashboard
      ├─ bugfix/fix-login
      └─ hotfix/critical-bug
```

### Comandos Git Comunes

```bash
# Crear feature branch
git checkout develop
git pull origin develop
git checkout -b feature/add-comments

# Hacer commits
git add .
git commit -m "feat: Add comment system for practices"

# Push
git push origin feature/add-comments

# Crear Pull Request en GitHub

# Actualizar desde develop
git checkout develop
git pull origin develop
git checkout feature/add-comments
git merge develop

# Después de merge
git checkout develop
git pull origin develop
git branch -d feature/add-comments
```

### Commit Message Convention

```
<type>(<scope>): <subject>

Types:
- feat: Nueva feature
- fix: Bug fix
- docs: Documentación
- style: Formateo, sin cambios de código
- refactor: Refactorización
- test: Agregar/modificar tests
- chore: Mantenimiento, configs

Examples:
feat(practices): Add comment system
fix(auth): Fix password reset email
docs(api): Update REST API documentation
refactor(repos): Simplify query optimization
test(practices): Add integration tests
```

---

## ⚡ Performance y Optimización

### Database Queries

**❌ N+1 Problem**:
```python
# Malo - genera N+1 queries
practices = Practice.objects.all()
for practice in practices:
    print(practice.student.user.email)  # Query por cada práctica
    print(practice.company.razon_social)  # Otro query
```

**✅ Optimizado**:
```python
# Bueno - 1 query con JOINs
practices = Practice.objects.select_related(
    'student__user',
    'company',
    'supervisor__user'
).all()

for practice in practices:
    print(practice.student.user.email)  # Sin query adicional
    print(practice.company.razon_social)  # Sin query adicional
```

### Prefetch Related

```python
# Para relaciones ManyToMany o reverse ForeignKey
practices = Practice.objects.prefetch_related(
    'documents',
    'activities',
    'comments'
).all()
```

### Database Indexes

```python
class Practice(models.Model):
    # ... campos ...
    
    class Meta:
        indexes = [
            models.Index(fields=['student', 'estado']),
            models.Index(fields=['company', 'fecha_inicio']),
            models.Index(fields=['-created_at']),
        ]
```

### Caching con Redis

```python
from django.core.cache import cache

def get_practice_statistics():
    """Obtiene estadísticas con cache."""
    cache_key = 'practice_statistics'
    
    # Intentar obtener del cache
    stats = cache.get(cache_key)
    
    if stats is None:
        # Calcular estadísticas (costoso)
        stats = {
            'total': Practice.objects.count(),
            'active': Practice.objects.filter(estado='IN_PROGRESS').count(),
            # ... más estadísticas
        }
        
        # Guardar en cache por 1 hora
        cache.set(cache_key, stats, 60 * 60)
    
    return stats
```

### Paginación

```python
from rest_framework.pagination import PageNumberPagination

class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
```

---

## 📚 Recursos Adicionales

- 📖 [Django Documentation](https://docs.djangoproject.com/)
- 📖 [DRF Documentation](https://www.django-rest-framework.org/)
- 📖 [GraphQL Python](https://docs.graphene-python.org/)
- 📖 [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- 📖 [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

**Universidad Peruana Unión**  
**Sistema de Gestión de Prácticas Profesionales**  
**Versión 2.0** - Octubre 2024
