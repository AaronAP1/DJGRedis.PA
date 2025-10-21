# 🧪 Guía de Testing - Sistema de Gestión de Prácticas Profesionales

## 📋 Tabla de Contenidos

- [Introducción](#introducción)
- [Configuración del Entorno](#configuración-del-entorno)
- [Tipos de Tests](#tipos-de-tests)
- [Ejecutar Tests](#ejecutar-tests)
- [Coverage (Cobertura)](#coverage-cobertura)
- [Fixtures y Factories](#fixtures-y-factories)
- [Mocking](#mocking)
- [Tests por Capa](#tests-por-capa)
- [Continuous Integration](#continuous-integration)

---

## 🎯 Introducción

El proyecto utiliza **pytest** como framework principal de testing, complementado con las herramientas de testing de Django.

### Filosofía de Testing

- **Test-Driven Development (TDD)**: Escribir tests antes del código cuando sea posible
- **Cobertura Mínima**: 80% del código debe estar cubierto
- **Tests Rápidos**: Los tests unitarios deben ejecutarse en < 1 segundo
- **Tests Aislados**: Cada test debe ser independiente

### Stack de Testing

- **pytest**: Framework de testing principal
- **pytest-django**: Integración con Django
- **factory-boy**: Factories para crear objetos de prueba
- **faker**: Generación de datos fake
- **coverage.py**: Análisis de cobertura
- **pytest-cov**: Plugin de coverage para pytest
- **mock**: Mocking y patching

---

## ⚙️ Configuración del Entorno

### 1. Instalar Dependencias

```bash
pip install -r requirements/development.txt
```

Esto instala:
```
pytest==7.4.3
pytest-django==4.7.0
pytest-cov==4.1.0
factory-boy==3.3.0
faker==20.1.0
```

### 2. Configuración de pytest

Archivo `pytest.ini` (ya configurado):

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --reuse-db
    --nomigrations
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --maxfail=5
    -v
testpaths = tests
```

### 3. Configuración de Coverage

Archivo `.coveragerc`:

```ini
[run]
source = src/
omit = 
    */migrations/*
    */tests/*
    */test_*.py
    */__pycache__/*
    */venv/*
    */env/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

---

## 🧪 Tipos de Tests

### 1. Tests Unitarios

Prueban **una sola unidad de código** aisladamente (función, método, clase).

**Características**:
- ✅ Rápidos (< 1 segundo)
- ✅ Sin dependencias externas (DB, Redis, APIs)
- ✅ Usan mocks para dependencias
- ✅ Alta cobertura de lógica de negocio

**Ejemplo**:

```python
# tests/unit/test_use_cases.py
import pytest
from unittest.mock import Mock, MagicMock
from decimal import Decimal
from src.application.use_cases.practices.validate_requirements import (
    ValidateRequirementsUseCase
)
from src.domain.exceptions import ValidationError

class TestValidateRequirementsUseCase:
    """Tests unitarios para validación de requisitos."""
    
    @pytest.fixture
    def mock_student(self):
        """Mock de estudiante válido."""
        student = Mock()
        student.semestre_actual = 7
        student.promedio_ponderado = Decimal('15.5')
        student.codigo_estudiante = '2024012345'
        return student
    
    @pytest.fixture
    def use_case(self):
        """Instancia del caso de uso."""
        return ValidateRequirementsUseCase()
    
    def test_validate_valid_student(self, use_case, mock_student):
        """Test: Estudiante válido pasa la validación."""
        # Act
        result = use_case.validate_student(mock_student)
        
        # Assert
        assert result is True
    
    def test_validate_student_low_semester(self, use_case, mock_student):
        """Test: Estudiante con semestre bajo falla."""
        # Arrange
        mock_student.semestre_actual = 4
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            use_case.validate_student(mock_student)
        
        assert "semestre 6 o superior" in str(exc_info.value)
    
    def test_validate_student_low_average(self, use_case, mock_student):
        """Test: Estudiante con promedio bajo falla."""
        # Arrange
        mock_student.promedio_ponderado = Decimal('10.5')
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            use_case.validate_student(mock_student)
        
        assert "promedio" in str(exc_info.value).lower()
```

### 2. Tests de Integración

Prueban la **interacción entre componentes** (con base de datos real).

**Características**:
- ✅ Más lentos que unitarios
- ✅ Usan base de datos de prueba
- ✅ Prueban repositories, serializers, viewsets
- ✅ Transacciones automáticas (rollback después)

**Ejemplo**:

```python
# tests/integration/test_repositories.py
import pytest
from django.test import TestCase
from src.domain.models import User, Student, Practice, Company
from src.adapters.secondary.repositories.practice_repository import (
    DjangoPracticeRepository
)

@pytest.mark.django_db
class TestPracticeRepository:
    """Tests de integración para Practice Repository."""
    
    @pytest.fixture
    def student(self):
        """Crea estudiante de prueba."""
        user = User.objects.create_user(
            email='student@upeu.edu.pe',
            password='test123',
            first_name='Juan',
            last_name='Pérez',
            role='PRACTICANTE'
        )
        return Student.objects.create(
            user=user,
            codigo_estudiante='2024012345',
            escuela_profesional='Ingeniería de Sistemas',
            semestre_actual=7,
            promedio_ponderado=15.0
        )
    
    @pytest.fixture
    def company(self):
        """Crea empresa de prueba."""
        return Company.objects.create(
            razon_social='Test Corp SAC',
            ruc='20123456789',
            sector_economico='Tecnología',
            validated=True,
            estado='ACTIVE'
        )
    
    @pytest.fixture
    def repository(self):
        """Instancia del repositorio."""
        return DjangoPracticeRepository()
    
    def test_save_practice(self, repository, student, company):
        """Test: Guardar una práctica."""
        # Arrange
        practice = Practice(
            student=student,
            company=company,
            area='Desarrollo Web',
            horas_requeridas=480,
            estado='DRAFT'
        )
        
        # Act
        saved = repository.save(practice)
        
        # Assert
        assert saved.id is not None
        assert saved.student == student
        assert saved.company == company
    
    def test_find_by_id(self, repository, student, company):
        """Test: Buscar práctica por ID."""
        # Arrange
        practice = Practice.objects.create(
            student=student,
            company=company,
            area='Testing',
            horas_requeridas=480
        )
        
        # Act
        found = repository.find_by_id(practice.id)
        
        # Assert
        assert found is not None
        assert found.id == practice.id
        assert found.area == 'Testing'
    
    def test_find_by_student(self, repository, student, company):
        """Test: Buscar prácticas por estudiante."""
        # Arrange
        Practice.objects.create(
            student=student,
            company=company,
            area='Area 1',
            horas_requeridas=480
        )
        Practice.objects.create(
            student=student,
            company=company,
            area='Area 2',
            horas_requeridas=480
        )
        
        # Act
        practices = repository.find_by_student(student.id)
        
        # Assert
        assert len(practices) == 2
        assert all(p.student == student for p in practices)
```

### 3. Tests End-to-End (E2E)

Prueban **flujos completos** del sistema.

**Ejemplo**:

```python
# tests/e2e/test_practice_flow.py
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestPracticeFlow:
    """Tests E2E del flujo completo de práctica."""
    
    @pytest.fixture
    def client(self):
        return APIClient()
    
    @pytest.fixture
    def coordinator(self):
        return User.objects.create_user(
            email='coordinator@upeu.edu.pe',
            password='test123',
            role='COORDINADOR'
        )
    
    @pytest.fixture
    def student(self):
        user = User.objects.create_user(
            email='student@upeu.edu.pe',
            password='test123',
            role='PRACTICANTE'
        )
        return Student.objects.create(
            user=user,
            codigo_estudiante='2024012345',
            semestre_actual=7,
            promedio_ponderado=15.0
        )
    
    def test_complete_practice_flow(
        self,
        client,
        coordinator,
        student,
        company
    ):
        """Test: Flujo completo desde solicitud hasta aprobación."""
        
        # 1. Estudiante crea solicitud
        client.force_authenticate(user=student.user)
        response = client.post('/api/v2/practices/', {
            'student_id': student.id,
            'company_id': company.id,
            'area': 'Desarrollo Web',
            'fecha_inicio': '2024-03-01',
            'horas_requeridas': 480
        })
        assert response.status_code == 201
        practice_id = response.data['id']
        
        # 2. Coordinador aprueba
        client.force_authenticate(user=coordinator)
        response = client.post(
            f'/api/v2/practices/{practice_id}/approve/',
            {'supervisor_id': supervisor.id}
        )
        assert response.status_code == 200
        
        # 3. Verificar estado
        response = client.get(f'/api/v2/practices/{practice_id}/')
        assert response.data['estado'] == 'APPROVED'
```

---

## ▶️ Ejecutar Tests

### Comandos Básicos

```bash
# Todos los tests
pytest

# Tests específicos por archivo
pytest tests/unit/test_use_cases.py

# Tests específicos por clase
pytest tests/unit/test_use_cases.py::TestValidateRequirementsUseCase

# Tests específicos por método
pytest tests/unit/test_use_cases.py::TestValidateRequirementsUseCase::test_validate_valid_student

# Con output detallado
pytest -v

# Con output muy detallado
pytest -vv

# Mostrar print statements
pytest -s

# Detener en el primer fallo
pytest -x

# Detener después de N fallos
pytest --maxfail=3

# Solo tests que fallaron la última vez
pytest --lf

# Tests en paralelo (requiere pytest-xdist)
pytest -n auto

# Tests con palabra clave
pytest -k "validate"
```

### Tests por Categoría

```bash
# Solo tests unitarios
pytest tests/unit/

# Solo tests de integración
pytest tests/integration/

# Solo tests E2E
pytest tests/e2e/

# Excluir tests lentos
pytest -m "not slow"

# Solo tests marcados como "smoke"
pytest -m smoke
```

### Tests con Django

```bash
# Con django-admin
python manage.py test

# Test específico
python manage.py test tests.integration.test_repositories.TestPracticeRepository

# Con cobertura
python manage.py test --with-coverage

# Mantener base de datos
python manage.py test --keepdb
```

---

## 📊 Coverage (Cobertura)

### Generar Reporte de Cobertura

```bash
# Con pytest
pytest --cov=src --cov-report=html --cov-report=term

# Abrir reporte HTML
firefox htmlcov/index.html  # Linux
open htmlcov/index.html     # Mac
start htmlcov/index.html    # Windows
```

### Interpretar Resultados

```
Name                                      Stmts   Miss  Cover
-------------------------------------------------------------
src/__init__.py                               0      0   100%
src/domain/entities.py                      145     12    92%
src/domain/models.py                        320     45    86%
src/application/use_cases/practices.py      180     25    86%
src/adapters/primary/rest_api/views.py      250     38    85%
-------------------------------------------------------------
TOTAL                                      2850    350    88%
```

**Métricas**:
- **Stmts**: Líneas de código totales
- **Miss**: Líneas no cubiertas por tests
- **Cover**: Porcentaje de cobertura

**Objetivos**:
- ✅ Dominio y Casos de Uso: >90%
- ✅ Adaptadores: >80%
- ✅ Total del proyecto: >80%

### Configurar Umbrales

En `pytest.ini`:

```ini
[pytest]
addopts = 
    --cov=src
    --cov-fail-under=80
```

---

## 🏭 Fixtures y Factories

### Fixtures con pytest

```python
# tests/conftest.py
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def user():
    """Usuario básico."""
    return User.objects.create_user(
        email='test@upeu.edu.pe',
        password='test123',
        role='PRACTICANTE'
    )

@pytest.fixture
def coordinator():
    """Usuario coordinador."""
    return User.objects.create_user(
        email='coordinator@upeu.edu.pe',
        password='test123',
        role='COORDINADOR'
    )

@pytest.fixture
def api_client():
    """Cliente de API REST."""
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, user):
    """Cliente autenticado."""
    api_client.force_authenticate(user=user)
    return api_client
```

### Factories con factory_boy

```python
# tests/factories.py
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from src.domain.models import User, Student, Company, Practice

fake = Faker('es_ES')

class UserFactory(DjangoModelFactory):
    """Factory para User."""
    
    class Meta:
        model = User
    
    email = factory.LazyAttribute(lambda _: fake.email())
    first_name = factory.LazyAttribute(lambda _: fake.first_name())
    last_name = factory.LazyAttribute(lambda _: fake.last_name())
    role = 'PRACTICANTE'
    is_active = True

class StudentFactory(DjangoModelFactory):
    """Factory para Student."""
    
    class Meta:
        model = Student
    
    user = factory.SubFactory(UserFactory, role='PRACTICANTE')
    codigo_estudiante = factory.LazyAttribute(
        lambda _: f"2024{fake.random_number(digits=6, fix_len=True)}"
    )
    escuela_profesional = 'Ingeniería de Sistemas'
    semestre_actual = 7
    promedio_ponderado = factory.LazyAttribute(
        lambda _: fake.pydecimal(
            left_digits=2,
            right_digits=1,
            min_value=12,
            max_value=18
        )
    )

class CompanyFactory(DjangoModelFactory):
    """Factory para Company."""
    
    class Meta:
        model = Company
    
    razon_social = factory.LazyAttribute(lambda _: f"{fake.company()} SAC")
    ruc = factory.LazyAttribute(
        lambda _: f"20{fake.random_number(digits=9, fix_len=True)}"
    )
    sector_economico = 'Tecnología'
    direccion = factory.LazyAttribute(lambda _: fake.address())
    telefono = factory.LazyAttribute(lambda _: fake.phone_number())
    email = factory.LazyAttribute(lambda _: fake.company_email())
    validated = True
    estado = 'ACTIVE'

class PracticeFactory(DjangoModelFactory):
    """Factory para Practice."""
    
    class Meta:
        model = Practice
    
    student = factory.SubFactory(StudentFactory)
    company = factory.SubFactory(CompanyFactory)
    area = 'Desarrollo de Software'
    horas_requeridas = 480
    estado = 'DRAFT'
```

### Usar Factories en Tests

```python
# tests/integration/test_with_factories.py
import pytest
from tests.factories import UserFactory, StudentFactory, PracticeFactory

@pytest.mark.django_db
class TestWithFactories:
    
    def test_create_practice_with_factories(self):
        """Test: Crear práctica con factories."""
        # Arrange
        practice = PracticeFactory()
        
        # Assert
        assert practice.id is not None
        assert practice.student is not None
        assert practice.company is not None
    
    def test_create_multiple_students(self):
        """Test: Crear múltiples estudiantes."""
        # Arrange
        students = StudentFactory.create_batch(10)
        
        # Assert
        assert len(students) == 10
        assert all(s.semestre_actual == 7 for s in students)
    
    def test_override_factory_attributes(self):
        """Test: Override de atributos."""
        # Arrange
        student = StudentFactory(
            semestre_actual=10,
            promedio_ponderado=18.0
        )
        
        # Assert
        assert student.semestre_actual == 10
        assert student.promedio_ponderado == 18.0
```

---

## 🎭 Mocking

### Mock Básico

```python
from unittest.mock import Mock, patch

def test_with_mock():
    """Test con mock básico."""
    # Crear mock
    mock_repo = Mock()
    mock_repo.find_by_id.return_value = Practice(id=1, area='Test')
    
    # Usar mock
    practice = mock_repo.find_by_id(1)
    
    # Verificar
    assert practice.id == 1
    mock_repo.find_by_id.assert_called_once_with(1)
```

### Patch Decorador

```python
@patch('src.adapters.secondary.email.service.EmailService')
def test_with_patch(mock_email):
    """Test con patch como decorador."""
    # Configurar mock
    mock_email.return_value.send_email.return_value = True
    
    # Ejecutar código que usa EmailService
    result = send_welcome_email(user)
    
    # Verificar
    assert result is True
    mock_email.return_value.send_email.assert_called_once()
```

### Context Manager

```python
def test_with_patch_context_manager():
    """Test con patch como context manager."""
    with patch('src.domain.models.Practice.objects') as mock_objects:
        mock_objects.filter.return_value.count.return_value = 5
        
        # Código que usa Practice.objects.filter()
        count = Practice.objects.filter(estado='ACTIVE').count()
        
        assert count == 5
```

### Mock Async Functions

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_async_function():
    """Test de función asíncrona."""
    # Mock async
    mock_service = AsyncMock()
    mock_service.fetch_data.return_value = {'result': 'ok'}
    
    # Llamar
    result = await mock_service.fetch_data()
    
    # Verificar
    assert result['result'] == 'ok'
    mock_service.fetch_data.assert_called_once()
```

---

## 🏛️ Tests por Capa

### Tests de Dominio

```python
# tests/unit/domain/test_entities.py
from src.domain.entities import Practice
from decimal import Decimal

def test_practice_progress_percentage():
    """Test: Cálculo de porcentaje de progreso."""
    practice = Practice(
        horas_completadas=240,
        horas_requeridas=480
    )
    
    assert practice.progress_percentage == 50.0

def test_practice_is_completed():
    """Test: Verificar si práctica está completada."""
    practice = Practice(
        horas_completadas=480,
        horas_requeridas=480
    )
    
    assert practice.is_completed is True
```

### Tests de Aplicación (Use Cases)

```python
# tests/unit/application/test_create_practice_use_case.py
from unittest.mock import Mock
from src.application.use_cases.practices.create_practice import (
    CreatePracticeUseCase,
    CreatePracticeRequest
)

def test_create_practice_use_case():
    """Test del caso de uso de crear práctica."""
    # Arrange
    mock_repo = Mock()
    use_case = CreatePracticeUseCase(practice_repo=mock_repo)
    
    request = CreatePracticeRequest(
        student_id=1,
        company_id=1,
        area='Testing'
    )
    
    # Act
    use_case.execute(request)
    
    # Assert
    mock_repo.save.assert_called_once()
```

### Tests de Adaptadores (ViewSets)

```python
# tests/integration/adapters/test_practice_viewset.py
import pytest
from rest_framework.test import APIClient

@pytest.mark.django_db
class TestPracticeViewSet:
    
    def test_list_practices(self, authenticated_client):
        """Test: Listar prácticas."""
        response = authenticated_client.get('/api/v2/practices/')
        
        assert response.status_code == 200
        assert 'results' in response.data
```

---

## 🔄 Continuous Integration

### GitHub Actions

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements/development.txt
      
      - name: Run tests
        run: |
          pytest --cov=src --cov-report=xml
        env:
          DATABASE_URL: postgres://postgres:postgres@localhost/test_db
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## 📚 Recursos

- 📖 [pytest Documentation](https://docs.pytest.org/)
- 📖 [Django Testing](https://docs.djangoproject.com/en/5.0/topics/testing/)
- 📖 [factory_boy](https://factoryboy.readthedocs.io/)
- 📖 [Coverage.py](https://coverage.readthedocs.io/)

---

**Universidad Peruana Unión**  
**Sistema de Gestión de Prácticas Profesionales**  
**Versión 2.0** - Octubre 2024
