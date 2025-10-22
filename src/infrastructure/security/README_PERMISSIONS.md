# 🔒 Sistema de Permisos por Rol

Sistema completo de autorización basado en roles para el sistema de gestión de prácticas profesionales.

## 📋 Tabla de Contenidos

- [Roles del Sistema](#roles-del-sistema)
- [Permisos REST API](#permisos-rest-api)
- [Permisos GraphQL](#permisos-graphql)
- [Ejemplos de Uso](#ejemplos-de-uso)
- [Helpers de Permisos](#helpers-de-permisos)

---

## 👥 Roles del Sistema

| Rol | Código | Descripción |
|-----|--------|-------------|
| **Practicante** | `PRACTICANTE` | Estudiante realizando prácticas |
| **Supervisor** | `SUPERVISOR` | Supervisor de empresa |
| **Coordinador** | `COORDINADOR` | Coordinador académico |
| **Secretaria** | `SECRETARIA` | Personal administrativo |
| **Administrador** | `ADMINISTRADOR` | Administrador del sistema |

---

## 🛡️ Permisos REST API

### Clases de Permisos Disponibles

#### **Permisos Base por Rol**

```python
from src.infrastructure.security.permissions import (
    IsAdministrador,
    IsCoordinador,
    IsSecretaria,
    IsSupervisor,
    IsPracticante,
)

# Uso en ViewSet
class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdministrador]
```

#### **Permisos Combinados**

```python
from src.infrastructure.security.permissions import (
    IsAdminOrCoordinador,
    IsAdminOrCoordinadorOrSecretaria,
    IsStaffMember,  # Admin, Coordinador o Secretaria
)
```

#### **Permisos de Propiedad**

```python
from src.infrastructure.security.permissions import (
    IsOwner,              # Solo el propietario
    IsOwnerOrAdmin,       # Propietario o Admin
    IsOwnerOrStaff,       # Propietario o Staff
)
```

#### **Permisos Específicos por Entidad**

```python
from src.infrastructure.security.permissions import (
    # Usuarios
    CanManageUsers,
    CanViewOwnProfile,
    CanUpdateOwnProfile,
    
    # Estudiantes
    CanManageStudents,
    CanViewStudent,
    
    # Empresas
    CanManageCompanies,
    CanViewCompany,
    CanValidateCompany,
    
    # Prácticas
    CanCreatePractice,
    CanViewPractice,
    CanUpdatePractice,
    CanApprovePractice,
    CanEvaluatePractice,
    
    # Documentos
    CanUploadDocument,
    CanViewDocument,
    CanDeleteDocument,
    CanApproveDocument,
    
    # Notificaciones
    CanViewNotification,
    CanCreateNotification,
)
```

### Ejemplos de Uso en ViewSets

#### **Ejemplo 1: ViewSet con Múltiples Permisos**

```python
from rest_framework import viewsets
from src.infrastructure.security.permissions import (
    IsAuthenticated,
    CanViewPractice,
    CanUpdatePractice,
)

class PracticeViewSet(viewsets.ModelViewSet):
    queryset = Practice.objects.all()
    serializer_class = PracticeSerializer
    
    def get_permissions(self):
        """Permisos dinámicos según la acción."""
        if self.action == 'list':
            permission_classes = [IsAuthenticated]
        elif self.action == 'retrieve':
            permission_classes = [CanViewPractice]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [CanUpdatePractice]
        elif self.action == 'destroy':
            permission_classes = [IsAdministrador]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
```

#### **Ejemplo 2: Acción Personalizada con Permiso**

```python
from rest_framework.decorators import action
from rest_framework.response import Response
from src.infrastructure.security.permissions import CanApprovePractice

class PracticeViewSet(viewsets.ModelViewSet):
    
    @action(
        detail=True, 
        methods=['post'],
        permission_classes=[CanApprovePractice]
    )
    def approve(self, request, pk=None):
        """Aprobar una práctica (solo COORDINADOR o ADMIN)."""
        practice = self.get_object()
        practice.status = 'APPROVED'
        practice.save()
        return Response({'status': 'aprobada'})
```

#### **Ejemplo 3: Filtrado por Rol**

```python
class PracticeViewSet(viewsets.ModelViewSet):
    
    def get_queryset(self):
        """Filtra las prácticas según el rol del usuario."""
        user = self.request.user
        
        # Staff puede ver todas
        if user.role in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']:
            return Practice.objects.all()
        
        # Practicante solo ve las suyas
        if user.role == 'PRACTICANTE':
            return Practice.objects.filter(student__user=user)
        
        # Supervisor solo ve las asignadas
        if user.role == 'SUPERVISOR' and hasattr(user, 'supervisor_profile'):
            return Practice.objects.filter(supervisor=user.supervisor_profile)
        
        return Practice.objects.none()
```

---

## 🔷 Permisos GraphQL

### Decoradores Disponibles

#### **Decoradores Base**

```python
from src.infrastructure.security.decorators import (
    login_required,           # Requiere autenticación
    role_required,           # Requiere rol(es) específico(s)
)
```

#### **Decoradores por Rol**

```python
from src.infrastructure.security.decorators import (
    admin_required,
    coordinator_required,
    staff_required,
    practicante_required,
    supervisor_required,
)
```

#### **Decoradores Combinados**

```python
from src.infrastructure.security.decorators import (
    admin_or_coordinator_required,
    admin_or_coordinator_or_secretary_required,
)
```

### Ejemplos de Uso en Queries

```python
from src.infrastructure.security.decorators import login_required, staff_required

class Query(graphene.ObjectType):
    
    # Requiere solo autenticación
    @login_required
    def resolve_my_practices(self, info):
        user = info.context.user
        return Practice.objects.filter(student__user=user)
    
    # Requiere rol específico
    @staff_required
    def resolve_all_practices(self, info):
        return Practice.objects.all()
    
    # Requiere múltiples roles
    @role_required('ADMINISTRADOR', 'COORDINADOR')
    def resolve_pending_approvals(self, info):
        return Practice.objects.filter(status='PENDING')
```

### Ejemplos de Uso en Mutations

```python
from src.infrastructure.security.decorators import (
    login_required,
    admin_or_coordinator_required,
)
from src.infrastructure.security.permission_helpers import (
    can_update_practice,
)
from graphql import GraphQLError

class ApprovePracticeMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    practice = graphene.Field(PracticeType)
    
    @admin_or_coordinator_required
    def mutate(self, info, id):
        """Solo ADMIN o COORDINADOR pueden aprobar."""
        practice = Practice.objects.get(id=id)
        practice.status = 'APPROVED'
        practice.save()
        return ApprovePracticeMutation(success=True, practice=practice)


class UpdatePracticeMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        titulo = graphene.String()
        descripcion = graphene.String()
    
    success = graphene.Boolean()
    practice = graphene.Field(PracticeType)
    
    @login_required
    def mutate(self, info, id, **kwargs):
        """Actualizar práctica con validación de permisos."""
        user = info.context.user
        practice = Practice.objects.get(id=id)
        
        # Verificar permisos usando helper
        if not can_update_practice(user, practice):
            raise GraphQLError('No tienes permiso para actualizar esta práctica')
        
        # Actualizar campos
        for field, value in kwargs.items():
            setattr(practice, field, value)
        
        practice.save()
        return UpdatePracticeMutation(success=True, practice=practice)
```

---

## 🔧 Helpers de Permisos

Los helpers son funciones que verifican permisos y pueden usarse en cualquier contexto (views, resolvers, tasks, etc.).

```python
from src.infrastructure.security.permission_helpers import (
    # Verificadores de rol
    is_administrador,
    is_coordinador,
    is_secretaria,
    is_supervisor,
    is_practicante,
    is_staff,
    
    # Verificadores sobre usuarios
    can_view_user,
    can_update_user,
    can_delete_user,
    
    # Verificadores sobre estudiantes
    can_view_student,
    can_update_student,
    can_delete_student,
    
    # Verificadores sobre empresas
    can_view_company,
    can_update_company,
    can_validate_company,
    
    # Verificadores sobre prácticas
    can_view_practice,
    can_update_practice,
    can_approve_practice,
    can_evaluate_practice,
    can_change_practice_status,
    
    # Verificadores sobre documentos
    can_view_document,
    can_upload_document,
    can_delete_document,
    can_approve_document,
    
    # Verificadores sobre notificaciones
    can_view_notification,
    can_create_notification,
    
    # Verificadores de reportes
    can_view_all_statistics,
    can_view_reports,
    can_export_data,
)
```

### Ejemplo de Uso de Helpers

```python
from src.infrastructure.security.permission_helpers import (
    can_update_practice,
    is_staff,
)

def my_custom_function(user, practice):
    """Función personalizada que necesita verificar permisos."""
    
    # Verificar si puede actualizar
    if not can_update_practice(user, practice):
        raise PermissionError('No puedes actualizar esta práctica')
    
    # Verificar si es staff para mostrar información adicional
    if is_staff(user):
        # Mostrar datos sensibles
        pass
    
    # Continuar con la lógica...
```

---

## 📊 Matriz de Permisos Completa

### **PRACTICANTE**

| Recurso | Crear | Listar | Ver | Actualizar | Eliminar |
|---------|-------|--------|-----|------------|----------|
| Users | ❌ | ❌ | ✅ Propio | ✅ Propio | ❌ |
| Students | ❌ | ❌ | ✅ Propio | ✅ Propio | ❌ |
| Companies | ❌ | ✅ Activas | ✅ | ❌ | ❌ |
| Supervisors | ❌ | ✅ | ✅ | ❌ | ❌ |
| Practices | ✅ | ✅ Propias | ✅ Propias | ✅ DRAFT | ❌ |
| Documents | ✅ | ✅ Propios | ✅ Propios | ❌ | ✅ No aprobados |
| Notifications | ❌ | ✅ Propias | ✅ Propias | ✅ Leer | ❌ |

### **SUPERVISOR**

| Recurso | Crear | Listar | Ver | Actualizar | Eliminar |
|---------|-------|--------|-----|------------|----------|
| Users | ❌ | ❌ | ✅ Propio | ✅ Propio | ❌ |
| Students | ❌ | ✅ Asignados | ✅ Asignados | ❌ | ❌ |
| Companies | ❌ | ❌ | ✅ Propia | ✅ Propia | ❌ |
| Supervisors | ❌ | ❌ | ✅ Propio | ✅ Propio | ❌ |
| Practices | ❌ | ✅ Asignadas | ✅ Asignadas | ✅ Evaluar | ❌ |
| Documents | ❌ | ✅ Asignados | ✅ Asignados | ❌ | ❌ |
| Notifications | ❌ | ✅ Propias | ✅ Propias | ✅ Leer | ❌ |

### **COORDINADOR**

| Recurso | Crear | Listar | Ver | Actualizar | Eliminar |
|---------|-------|--------|-----|------------|----------|
| Users | ✅ | ✅ | ✅ | ✅ | ❌ |
| Students | ✅ | ✅ | ✅ | ✅ | ❌ |
| Companies | ✅ | ✅ | ✅ | ✅ Validar | ❌ |
| Supervisors | ✅ | ✅ | ✅ | ✅ | ❌ |
| Practices | ✅ | ✅ | ✅ | ✅ Aprobar | ❌ |
| Documents | ❌ | ✅ | ✅ | ✅ Aprobar | ❌ |
| Notifications | ✅ | ✅ | ✅ | ❌ | ✅ |

### **SECRETARIA**

| Recurso | Crear | Listar | Ver | Actualizar | Eliminar |
|---------|-------|--------|-----|------------|----------|
| Users | ✅ | ✅ | ✅ | ✅ Básico | ❌ |
| Students | ✅ | ✅ | ✅ | ✅ | ❌ |
| Companies | ✅ | ✅ | ✅ | ✅ Básico | ❌ |
| Supervisors | ✅ | ✅ | ✅ | ✅ | ❌ |
| Practices | ❌ | ✅ | ✅ | ✅ Estado | ❌ |
| Documents | ✅ | ✅ | ✅ | ✅ Aprobar | ❌ |
| Notifications | ✅ | ✅ | ✅ | ❌ | ✅ |

### **ADMINISTRADOR**

| Recurso | Acceso |
|---------|--------|
| **TODO** | ✅ **ACCESO COMPLETO** |

---

## 🎯 Mejores Prácticas

### 1. **Siempre Verificar Autenticación Primero**

```python
# ❌ Mal
if user.role == 'ADMINISTRADOR':
    # ...

# ✅ Bien
if user and user.is_authenticated and user.role == 'ADMINISTRADOR':
    # ...
```

### 2. **Usar Helpers en Lugar de Lógica Directa**

```python
# ❌ Mal
if user.role in ['ADMINISTRADOR', 'COORDINADOR', 'SECRETARIA']:
    # ...

# ✅ Bien
from src.infrastructure.security.permission_helpers import is_staff

if is_staff(user):
    # ...
```

### 3. **Combinar Permisos en ViewSets**

```python
# ✅ Combinar múltiples checks
permission_classes = [IsAuthenticated, CanViewPractice]
```

### 4. **Filtrar QuerySets por Rol**

```python
# ✅ Siempre filtrar datos según permisos
def get_queryset(self):
    user = self.request.user
    if is_staff(user):
        return Practice.objects.all()
    return Practice.objects.filter(student__user=user)
```

### 5. **Validar Permisos de Objeto**

```python
# ✅ Usar has_object_permission
def has_object_permission(self, request, view, obj):
    return can_update_practice(request.user, obj)
```

---

## 🚨 Manejo de Errores

### REST API

```python
from rest_framework.exceptions import PermissionDenied

def my_view(request):
    if not can_do_something(request.user):
        raise PermissionDenied('No tienes permiso para realizar esta acción')
```

### GraphQL

```python
from graphql import GraphQLError

def resolve_something(self, info):
    if not can_do_something(info.context.user):
        raise GraphQLError('No tienes permiso para realizar esta acción')
```

---

## 📝 Testing de Permisos

```python
from django.test import TestCase
from src.infrastructure.security.permission_helpers import can_update_practice

class PermissionTests(TestCase):
    
    def test_practicante_can_update_own_draft_practice(self):
        """Practicante puede actualizar su práctica en DRAFT."""
        practice = Practice.objects.create(
            student=self.student,
            status='DRAFT'
        )
        
        self.assertTrue(
            can_update_practice(self.practicante_user, practice)
        )
    
    def test_practicante_cannot_update_approved_practice(self):
        """Practicante NO puede actualizar práctica aprobada."""
        practice = Practice.objects.create(
            student=self.student,
            status='APPROVED'
        )
        
        self.assertFalse(
            can_update_practice(self.practicante_user, practice)
        )
```

---

## 📚 Recursos Adicionales

- **Documentación DRF Permissions:** https://www.django-rest-framework.org/api-guide/permissions/
- **GraphQL Error Handling:** https://graphql.org/learn/validation/
- **Django Authentication:** https://docs.djangoproject.com/en/5.0/topics/auth/

---

## ✅ Checklist de Implementación

- [x] Clases de permisos REST implementadas
- [x] Helpers de permisos implementados
- [x] Decoradores GraphQL implementados
- [x] Documentación completa
- [ ] Tests unitarios de permisos
- [ ] Integración en ViewSets
- [ ] Integración en resolvers GraphQL
- [ ] Validación en producción
