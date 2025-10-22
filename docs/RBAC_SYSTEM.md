# 🔐 Sistema RBAC - Roles y Permisos

## 📋 Resumen de Implementación - Fase 2

Sistema completo de **Role-Based Access Control (RBAC)** implementado para el sistema de gestión de prácticas profesionales.

---

## 🎯 Componentes Implementados

### **1. Serializers de Seguridad**
**Archivo**: `src/adapters/primary/rest_api/serializers.py`

#### Serializers creados:
- ✅ **PermissionSerializer** - Detalles completos de permisos
- ✅ **PermissionListSerializer** - Vista resumida para listados
- ✅ **RoleSerializer** - Roles con permisos anidados
- ✅ **RoleListSerializer** - Vista resumida de roles
- ✅ **RoleCreateSerializer** - Creación de roles con permisos
- ✅ **RolePermissionSerializer** - Relación Role-Permission
- ✅ **UserPermissionSerializer** - Overrides de permisos
- ✅ **UserPermissionCreateSerializer** - Crear overrides

---

### **2. RoleViewSet - Gestión de Roles**
**Archivo**: `src/adapters/primary/rest_api/roles/viewset.py`

#### Endpoints CRUD:
```
GET    /api/v2/roles/                    # Lista de roles
GET    /api/v2/roles/{id}/               # Detalle de rol
POST   /api/v2/roles/                    # Crear rol (admin only)
PUT    /api/v2/roles/{id}/               # Actualizar rol (admin only)
PATCH  /api/v2/roles/{id}/               # Actualización parcial (admin only)
DELETE /api/v2/roles/{id}/               # Desactivar rol (admin only)
```

#### Custom Actions:
```
GET    /api/v2/roles/{id}/permissions/           # Permisos del rol
GET    /api/v2/roles/{id}/users/                 # Usuarios con este rol
POST   /api/v2/roles/{id}/add-permission/        # Agregar permiso (admin only)
DELETE /api/v2/roles/{id}/remove-permission/     # Remover permiso (admin only)
```

#### Características:
- ✅ CRUD completo con validaciones
- ✅ Gestión de permisos por rol
- ✅ Protección de roles del sistema (no se pueden modificar/eliminar)
- ✅ Soft delete (desactivación)
- ✅ Filtros por `is_active` y `is_system`
- ✅ Documentación OpenAPI completa

---

### **3. PermissionViewSet - Gestión de Permisos**
**Archivo**: `src/adapters/primary/rest_api/permissions/viewset.py`

#### Endpoints CRUD:
```
GET    /api/v2/permissions/              # Lista de permisos
GET    /api/v2/permissions/{id}/         # Detalle de permiso
POST   /api/v2/permissions/              # Crear permiso (admin only)
PUT    /api/v2/permissions/{id}/         # Actualizar permiso (admin only)
PATCH  /api/v2/permissions/{id}/         # Actualización parcial (admin only)
DELETE /api/v2/permissions/{id}/         # Desactivar permiso (admin only)
```

#### Custom Actions:
```
GET /api/v2/permissions/by-module/       # Permisos agrupados por módulo
GET /api/v2/permissions/{id}/roles/      # Roles que tienen este permiso
```

#### Características:
- ✅ Lectura para todos los usuarios autenticados
- ✅ Escritura solo para administradores
- ✅ Agrupación por módulo
- ✅ Búsqueda en code, name, description
- ✅ Filtros por `module`, `is_active`, `search`
- ✅ Soft delete

---

### **4. UserPermissionViewSet - Overrides de Permisos**
**Archivo**: `src/adapters/primary/rest_api/user_permissions/viewset.py`

#### Endpoints CRUD:
```
GET    /api/v2/user-permissions/                      # Lista overrides (admin only)
GET    /api/v2/user-permissions/{id}/                 # Detalle de override
POST   /api/v2/user-permissions/                      # Crear override (admin only)
DELETE /api/v2/user-permissions/{id}/                 # Eliminar override (admin only)
```

#### Custom Actions:
```
GET /api/v2/user-permissions/by-user/{user_id}/  # Overrides de un usuario
GET /api/v2/user-permissions/active/             # Overrides no expirados
GET /api/v2/user-permissions/expired/            # Overrides expirados
```

#### Tipos de Overrides:
1. **GRANT**: Otorga permiso adicional que no tiene por su rol
2. **REVOKE**: Revoca permiso que tiene por su rol

#### Características:
- ✅ Solo administradores pueden gestionar overrides
- ✅ Soporte para permisos temporales (con expiración)
- ✅ Auditoría completa (quién otorgó, cuándo, razón)
- ✅ Filtros por usuario, tipo, estado activo
- ✅ Validación de duplicados

---

### **5. UserViewSet - Endpoints Mejorados**
**Archivo**: `src/adapters/primary/rest_api/viewsets.py`

#### Nuevos Endpoints:
```
GET /api/v2/users/my-permissions/                # Mis permisos efectivos
GET /api/v2/users/available-avatars/             # Avatares de mi rol
GET /api/v2/users/{id}/effective-permissions/    # Permisos efectivos de usuario (admin only)
```

#### Endpoint `effective-permissions`:
Calcula permisos efectivos combinando:
1. Permisos del rol
2. Permisos GRANT (agregados)
3. Permisos REVOKE (removidos)

**Respuesta**:
```json
{
  "user": {
    "id": "uuid",
    "email": "user@upeu.edu.pe",
    "full_name": "Juan Pérez",
    "role": "PRACTICANTE"
  },
  "effective_permissions_count": 15,
  "permissions": [
    {
      "code": "PRACTICE.VIEW",
      "name": "Ver prácticas",
      "module": "practices",
      "source": "role",
      "status": "active"
    }
  ],
  "revoked_permissions": []
}
```

---

## 🗺️ Estructura de Directorios Creada

```
src/adapters/primary/rest_api/
├── avatars/
│   ├── __init__.py
│   └── viewset.py
├── roles/
│   ├── __init__.py
│   └── viewset.py
├── permissions/
│   ├── __init__.py
│   └── viewset.py
├── user_permissions/
│   ├── __init__.py
│   └── viewset.py
├── serializers.py (actualizado con serializers de seguridad)
├── viewsets.py (actualizado con endpoints de permisos)
└── urls_api_v2.py (actualizado con nuevos routers)
```

---

## 📊 Modelos de Base de Datos (ya existentes)

### **Avatar**
- `id` (UUID)
- `url` (URLField)
- `role` (CharField - PRACTICANTE, SUPERVISOR, etc.)
- `is_active` (Boolean)
- `created_at` (DateTime)

### **Role**
- `id` (UUID)
- `code` (CharField - único)
- `name` (CharField)
- `description` (TextField)
- `permissions` (ManyToMany → Permission)
- `is_active` (Boolean)
- `is_system` (Boolean)
- `created_at`, `updated_at` (DateTime)

### **Permission**
- `id` (UUID)
- `code` (CharField - único)
- `name` (CharField)
- `description` (TextField)
- `module` (CharField)
- `is_active` (Boolean)
- `created_at` (DateTime)

### **RolePermission** (Junction)
- `id` (PK)
- `role` (FK → Role)
- `permission` (FK → Permission)
- `granted_by` (FK → User)
- `granted_at` (DateTime)

### **UserPermission**
- `id` (PK)
- `user` (FK → User)
- `permission` (FK → Permission)
- `permission_type` (CharField - GRANT/REVOKE)
- `granted_by` (FK → User)
- `reason` (TextField)
- `granted_at` (DateTime)
- `expires_at` (DateTime - nullable)

---

## 🔒 Sistema de Permisos

### **Permisos por Endpoint**

#### Lectura (GET):
- **Roles**: Cualquier usuario autenticado
- **Permissions**: Cualquier usuario autenticado
- **Avatares**: Cualquier usuario autenticado
- **User Permissions**: Solo administradores

#### Escritura (POST/PUT/PATCH/DELETE):
- **Roles**: Solo administradores
- **Permissions**: Solo administradores
- **Avatares**: Solo administradores
- **User Permissions**: Solo administradores

### **Protecciones Especiales**:
1. ❌ No se pueden modificar/eliminar **roles del sistema** (`is_system=True`)
2. ✅ Eliminaciones son **soft delete** (marcan `is_active=False`)
3. ✅ Validación de **duplicados** en overrides
4. ✅ Soporte para **permisos temporales** con expiración

---

## 🚀 Flujos de Uso

### **1. Crear un nuevo rol con permisos**
```http
POST /api/v2/roles/
{
  "code": "JEFE_PRACTICAS",
  "name": "Jefe de Prácticas",
  "description": "Supervisor de múltiples prácticas",
  "is_active": true,
  "permission_ids": [
    "uuid-permission-1",
    "uuid-permission-2"
  ]
}
```

### **2. Agregar permiso a rol existente**
```http
POST /api/v2/roles/{role_id}/add-permission/
{
  "permission_id": "uuid-permission-3"
}
```

### **3. Otorgar permiso temporal a usuario**
```http
POST /api/v2/user-permissions/
{
  "user": "uuid-user",
  "permission": "uuid-permission",
  "permission_type": "GRANT",
  "reason": "Permiso temporal para proyecto especial",
  "expires_at": "2025-12-31T23:59:59Z"
}
```

### **4. Revocar permiso de rol a usuario**
```http
POST /api/v2/user-permissions/
{
  "user": "uuid-user",
  "permission": "uuid-permission",
  "permission_type": "REVOKE",
  "reason": "Usuario no debe ver información confidencial"
}
```

### **5. Ver permisos efectivos de usuario**
```http
GET /api/v2/users/{user_id}/effective-permissions/
```

---

## 📝 Validaciones Implementadas

### **RoleViewSet**:
- ✅ Código de rol único y en mayúsculas
- ✅ No modificar/eliminar roles del sistema
- ✅ Verificar que permiso exista antes de agregar
- ✅ Verificar que rol no tenga ya el permiso antes de agregar

### **PermissionViewSet**:
- ✅ Código único y convertido a mayúsculas
- ✅ Búsqueda flexible por code, name, description

### **UserPermissionViewSet**:
- ✅ No duplicar overrides para mismo usuario-permiso
- ✅ Verificar que permiso esté activo
- ✅ Validar fechas de expiración

---

## 🎨 Ejemplo de Respuestas

### **Permisos efectivos de usuario**:
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "estudiante@upeu.edu.pe",
    "full_name": "María García",
    "role": "PRACTICANTE"
  },
  "effective_permissions_count": 18,
  "permissions": [
    {
      "code": "PRACTICE.VIEW",
      "name": "Ver prácticas",
      "description": "Permite ver detalles de prácticas",
      "module": "practices",
      "source": "role",
      "role": "Practicante",
      "status": "active"
    },
    {
      "code": "REPORT.GENERATE",
      "name": "Generar reportes",
      "description": "Permite generar reportes especiales",
      "module": "reports",
      "source": "user_grant",
      "granted_at": "2025-10-15T10:00:00Z",
      "expires_at": "2025-12-31T23:59:59Z",
      "reason": "Proyecto de tesis requiere análisis de datos",
      "status": "granted"
    }
  ],
  "revoked_permissions": []
}
```

### **Permisos agrupados por módulo**:
```json
{
  "modules_count": 5,
  "total_permissions": 45,
  "modules": [
    {
      "module": "practices",
      "permissions_count": 12,
      "permissions": [
        {
          "id": "uuid",
          "code": "PRACTICE.VIEW",
          "name": "Ver prácticas",
          "description": "...",
          "is_active": true
        }
      ]
    },
    {
      "module": "companies",
      "permissions_count": 8,
      "permissions": [...]
    }
  ]
}
```

---

## 🧪 Para Probar

1. **Instalar dependencias** (si faltan):
   ```powershell
   pip install django-filter djangorestframework-simplejwt drf-spectacular
   ```

2. **Ejecutar servidor**:
   ```powershell
   python manage.py runserver
   ```

3. **Acceder a documentación**:
   - Swagger UI: http://localhost:8000/api/docs/
   - ReDoc: http://localhost:8000/api/redoc/
   - Schema JSON: http://localhost:8000/api/schema/
   - API Root v2: http://localhost:8000/api/v2/

4. **Endpoints nuevos**:
   - Roles: http://localhost:8000/api/v2/roles/
   - Permisos: http://localhost:8000/api/v2/permissions/
   - User Permissions: http://localhost:8000/api/v2/user-permissions/
   - Avatares: http://localhost:8000/api/v2/avatars/

---

## ✅ Checklist de Implementación

### **Fase 1** (Completada):
- [x] AvatarSerializer
- [x] UserDetailSerializer con avatar anidado
- [x] UserCreateSerializer con avatar
- [x] UserUpdateSerializer con avatar
- [x] AvatarViewSet con CRUD y custom actions
- [x] Registro en URLs
- [x] Endpoint `my_permissions` en UserViewSet
- [x] Endpoint `available_avatars` en UserViewSet

### **Fase 2** (Completada):
- [x] Serializers de seguridad (Role, Permission, UserPermission)
- [x] RoleViewSet completo
- [x] PermissionViewSet completo
- [x] UserPermissionViewSet completo
- [x] Registro de todos los ViewSets en router
- [x] Endpoint `effective_permissions` en UserViewSet

---

## 🎯 Próximos Pasos Sugeridos

1. **Crear permisos iniciales** (data migration)
2. **Asignar permisos a roles existentes**
3. **Implementar decorador `@permission_required`** para endpoints
4. **Agregar cache de permisos** en Redis
5. **Crear endpoints de auditoría** (quién cambió qué permisos)
6. **Tests unitarios** para ViewSets de seguridad

---

## 📚 Documentación Relacionada

- **Arquitectura Hexagonal**: Ver `docs/arquitectura/README.md`
- **Modelos de Dominio**: Ver `src/domain/entities.py`
- **Configuración de Permisos**: Ver `config/settings.py`
- **Postman Collection**: Ver `docs/Postman_Collection_DJGRedisPA.json`

---

**Desarrollado por**: Sistema de Gestión de Prácticas Profesionales UPEU  
**Fecha**: Octubre 2025  
**Versión**: 2.0 - Sistema RBAC Completo
