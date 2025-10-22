# Sistema de Roles y Permisos

## 📋 Descripción

Sistema completo de gestión de roles y permisos con capacidad de personalización por usuario individual.

## 🏗️ Arquitectura

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│    User     │────→│ UserPermission   │     │ Permission  │
│  (usuario)  │     │  (override)      │────→│  (permisos) │
└──────┬──────┘     └──────────────────┘     └──────┬──────┘
       │                                             │
       ↓                                             ↑
┌─────────────┐                          ┌──────────────────┐
│    Role     │─────────────────────────→│ RolePermission   │
│   (roles)   │                          │ (permisos x rol) │
└─────────────┘                          └──────────────────┘
```

## 📊 Tablas

### `permissions` - Permisos del sistema
- **id**: UUID
- **code**: Código único (ej: `users.create`)
- **name**: Nombre descriptivo
- **description**: Descripción opcional
- **module**: Módulo al que pertenece
- **is_active**: Estado activo/inactivo

### `roles` - Roles del sistema
- **id**: UUID
- **code**: Código único (ej: `ADMINISTRADOR`)
- **name**: Nombre del rol
- **description**: Descripción
- **is_active**: Estado activo/inactivo
- **is_system**: Si es un rol del sistema (no se puede eliminar)

### `role_permissions` - Permisos de cada rol
- **id**: UUID
- **role_id**: FK a Role
- **permission_id**: FK a Permission
- **granted_by**: Usuario que otorgó el permiso
- **granted_at**: Fecha de asignación

### `user_permissions` - Permisos personalizados por usuario
- **id**: UUID
- **user_id**: FK a User
- **permission_id**: FK a Permission
- **permission_type**: `GRANT` (otorgar) o `REVOKE` (revocar)
- **granted_by**: Quien otorgó/revocó
- **reason**: Motivo del cambio
- **expires_at**: Fecha de expiración (opcional)

## 👥 Roles Predefinidos

### 1. **ADMINISTRADOR**
- **Permisos**: Todos (40 permisos)
- **Descripción**: Acceso completo al sistema
- **Capacidades**:
  - Gestión de usuarios, roles y permisos
  - Configuración del sistema
  - Acceso a todas las funciones

### 2. **COORDINADOR**
- **Permisos**: 32 permisos
- **Descripción**: Gestiona prácticas, estudiantes y empresas
- **Capacidades**:
  - Ver usuarios
  - Gestión completa de estudiantes
  - Gestión completa de empresas y supervisores
  - Gestión completa de prácticas
  - Gestión de documentos
  - Reportes y estadísticas

### 3. **SECRETARIA**
- **Permisos**: 15 permisos
- **Descripción**: Gestión administrativa y documentación
- **Capacidades**:
  - Ver y editar usuarios/estudiantes
  - Ver y editar empresas
  - Ver y editar prácticas (todas)
  - Gestión completa de documentos
  - Crear notificaciones

### 4. **SUPERVISOR**
- **Permisos**: 6 permisos
- **Descripción**: Supervisa prácticas de su empresa
- **Capacidades**:
  - Ver y editar sus prácticas
  - Subir/descargar documentos
  - Ver notificaciones

### 5. **PRACTICANTE**
- **Permisos**: 5 permisos
- **Descripción**: Usuario estudiante en prácticas
- **Capacidades**:
  - Ver sus prácticas
  - Ver, subir y descargar documentos
  - Ver notificaciones

## 🔐 Permisos Disponibles (40)

### Usuarios (6)
- `users.view` - Ver usuarios
- `users.create` - Crear usuarios
- `users.edit` - Editar usuarios
- `users.delete` - Eliminar usuarios
- `users.import` - Importar usuarios
- `users.export` - Exportar usuarios

### Estudiantes (4)
- `students.view` - Ver estudiantes
- `students.create` - Crear estudiantes
- `students.edit` - Editar estudiantes
- `students.delete` - Eliminar estudiantes

### Empresas (5)
- `companies.view` - Ver empresas
- `companies.create` - Crear empresas
- `companies.edit` - Editar empresas
- `companies.delete` - Eliminar empresas
- `companies.validate` - Validar empresas

### Supervisores (4)
- `supervisors.view` - Ver supervisores
- `supervisors.create` - Crear supervisores
- `supervisors.edit` - Editar supervisores
- `supervisors.delete` - Eliminar supervisores

### Prácticas (7)
- `practices.view` - Ver prácticas propias
- `practices.view_all` - Ver todas las prácticas
- `practices.create` - Crear prácticas
- `practices.edit` - Editar prácticas
- `practices.delete` - Eliminar prácticas
- `practices.approve` - Aprobar prácticas
- `practices.cancel` - Cancelar prácticas

### Documentos (5)
- `documents.view` - Ver documentos
- `documents.upload` - Subir documentos
- `documents.download` - Descargar documentos
- `documents.delete` - Eliminar documentos
- `documents.approve` - Aprobar documentos

### Notificaciones (3)
- `notifications.view` - Ver notificaciones
- `notifications.create` - Crear notificaciones
- `notifications.send` - Enviar notificaciones

### Reportes (3)
- `reports.view` - Ver reportes
- `reports.export` - Exportar reportes
- `statistics.view` - Ver estadísticas

### Administración (3)
- `admin.roles` - Gestionar roles
- `admin.permissions` - Gestionar permisos
- `admin.settings` - Configuración del sistema

## 📝 API GraphQL

### Queries

#### Ver mis permisos
```graphql
query {
  myPermissionsInfo {
    role {
      id
      code
      name
    }
    rolePermissions {
      id
      code
      name
      module
    }
    customPermissions {
      id
      permission {
        code
        name
      }
      permissionType
      reason
      expiresAt
    }
    allPermissions
  }
}
```

#### Listar roles (ADMIN)
```graphql
query {
  roles {
    id
    code
    name
    description
    isActive
    isSystem
    permissionsCount
    usersCount
    permissions {
      id
      code
      name
      module
    }
  }
}
```

#### Ver permisos de un usuario (ADMIN)
```graphql
query {
  userPermissionsInfo(userId: "uuid-aqui") {
    role {
      code
      name
    }
    rolePermissions {
      code
      name
    }
    customPermissions {
      permission {
        code
        name
      }
      permissionType
    }
    allPermissions
  }
}
```

### Mutations

#### Crear rol (ADMIN)
```graphql
mutation {
  createRole(input: {
    code: "SUPERVISOR_PRACTICAS"
    name: "Supervisor de Prácticas"
    description: "Gestiona supervisión de prácticas"
    permissionIds: ["uuid1", "uuid2"]
  }) {
    success
    message
    role {
      id
      code
      name
    }
  }
}
```

#### Asignar rol a usuario (ADMIN)
```graphql
mutation {
  assignRoleToUser(
    userId: "user-uuid"
    roleId: "role-uuid"
  ) {
    success
    message
    user {
      id
      email
      roleObj {
        code
        name
      }
    }
  }
}
```

#### Otorgar permiso adicional (ADMIN)
```graphql
mutation {
  grantUserPermission(
    userId: "user-uuid"
    permissionId: "permission-uuid"
    reason: "Acceso temporal para auditoría"
    expiresInDays: 30
  ) {
    success
    message
  }
}
```

#### Revocar permiso (ADMIN)
```graphql
mutation {
  revokeUserPermission(
    userId: "user-uuid"
    permissionId: "permission-uuid"
    reason: "Restricción de seguridad"
  ) {
    success
    message
  }
}
```

## 🔧 Métodos del Modelo User

```python
# Obtener todos los permisos efectivos
user.get_all_permissions()
# → ['users.view', 'users.create', ...]

# Verificar permiso específico
user.has_permission('users.create')
# → True/False

# Verificar si tiene al menos uno
user.has_any_permission(['users.create', 'users.edit'])
# → True/False

# Verificar si tiene todos
user.has_all_permissions(['users.create', 'users.edit'])
# → True/False
```

## 🚀 Comandos Django

### Inicializar permisos y roles
```bash
python manage.py init_permissions
```

### Crear superusuario con rol ADMINISTRADOR
```bash
python manage.py createsuperuser
```

## 💡 Ejemplo de Uso

### Caso 1: Usuario con rol + permisos adicionales
```
Usuario: Juan Pérez
Rol: SECRETARIA (15 permisos base)
Permisos adicionales (GRANT):
  - users.delete (temporal, expira en 7 días)
  - practices.approve

Permisos finales: 17 permisos
```

### Caso 2: Usuario con rol + permisos revocados
```
Usuario: María García
Rol: COORDINADOR (32 permisos base)
Permisos revocados (REVOKE):
  - users.delete
  - practices.delete

Permisos finales: 30 permisos
```

## ⚠️ Consideraciones

1. **Roles del sistema** (`is_system=True`) no se pueden eliminar
2. **Permisos personalizados** tienen prioridad sobre permisos del rol
3. **GRANT** agrega permisos al usuario
4. **REVOKE** quita permisos del rol al usuario
5. Los permisos pueden tener **fecha de expiración**
6. Solo **ADMINISTRADORES** pueden gestionar roles y permisos

## 🔄 Migración de Datos Existentes

Los usuarios actuales tienen el campo `role` (legacy). Para migrarlos al nuevo sistema:

1. Ejecutar `init_permissions` para crear roles
2. Asignar `role_obj` basado en el `role` legacy
3. El campo `role` se mantiene por compatibilidad pero `role_obj` tiene prioridad

## 📚 Próximos Pasos

1. ✅ Modelos creados
2. ✅ Migraciones aplicadas
3. ✅ Permisos y roles inicializados
4. ✅ API GraphQL completa
5. ✅ Quickstart actualizado
6. 🔄 Migrar usuarios existentes a `role_obj`
7. 🔄 Implementar decoradores `@require_permission`
8. 🔄 Agregar UI de gestión en frontend
