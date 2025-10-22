# Comandos de Gestión de Usuarios y Roles - Sistema JWT PURO

## 📝 Diferencia entre `code` y `name` en Roles

### `code` (Código)
- **Propósito**: Identificador único técnico del rol
- **Formato**: MAYÚSCULAS con guiones bajos (ej: `ADMINISTRADOR`, `COORDINADOR`)
- **Uso**: Se usa en código Python, migraciones y lógica de negocio
- **Ejemplo**: `PRACTICANTE`
- **No se debe cambiar**: Es la clave primaria del rol en el sistema

### `name` (Nombre)
- **Propósito**: Nombre descriptivo para humanos
- **Formato**: Texto legible (ej: "Administrador", "Coordinador de Prácticas")
- **Uso**: Se muestra en la interfaz de usuario
- **Ejemplo**: `"Practicante"`
- **Se puede cambiar**: Es solo para visualización

### Ejemplo Visual:
```
┌─────────────────┬──────────────────────────┐
│ code            │ name                     │
├─────────────────┼──────────────────────────┤
│ ADMINISTRADOR   │ Administrador            │
│ COORDINADOR     │ Coordinador de Prácticas │
│ SECRETARIA      │ Secretaria               │
│ SUPERVISOR      │ Supervisor de Empresa    │
│ PRACTICANTE     │ Practicante              │
└─────────────────┴──────────────────────────┘
```

## 🔧 Comandos Disponibles

### 1. **Inicializar Permisos y Roles**
Crea los 40 permisos y 5 roles del sistema.

```bash
python manage.py init_permissions
```

**Salida esperada:**
```
✅ Permiso creado: users.view
✅ Permiso creado: users.create
...
✅ Rol creado: Administrador
     → 40 permisos asignados
...
✨ Inicialización completada exitosamente!
```

---

### 2. **Migrar Usuarios Existentes**
Migra usuarios que tienen `role` (legacy) pero no `role_obj` (nuevo sistema).

```bash
# Ver qué se haría (modo simulación)
python manage.py migrate_user_roles --dry-run

# Aplicar la migración
python manage.py migrate_user_roles
```

**Ejemplo de salida:**
```
🔄 Migrando usuarios a nuevo sistema de roles...
📊 Usuarios a migrar: 5

  ✅ practicante@test.upeu.edu.pe → Practicante
  ✅ supervisor@test.upeu.edu.pe → Supervisor de Empresa
  ✅ coordinador@test.upeu.edu.pe → Coordinador de Prácticas

📊 RESUMEN:
  • Total usuarios: 5
  • Migrados: 5
```

---

### 3. **Crear Usuarios de Prueba**
Crea un usuario por cada rol del sistema para testing.

```bash
# Crear usuarios con contraseña por defecto (Test1234)
python manage.py create_test_users

# Crear con contraseña personalizada
python manage.py create_test_users --password MiPass123

# Forzar recreación (elimina usuarios existentes)
python manage.py create_test_users --force
```

**Usuarios creados:**
```
✅ admin@test.upeu.edu.pe → Administrador
   Usuario: admin.test | Contraseña: Test1234

✅ coordinador@test.upeu.edu.pe → Coordinador de Prácticas
   Usuario: coordinador.test | Contraseña: Test1234

✅ secretaria@test.upeu.edu.pe → Secretaria
   Usuario: secretaria.test | Contraseña: Test1234

✅ supervisor@test.upeu.edu.pe → Supervisor de Empresa
   Usuario: supervisor.test | Contraseña: Test1234

✅ practicante@test.upeu.edu.pe → Practicante
   Usuario: practicante.test | Contraseña: Test1234
```

---

### 4. **Limpiar Tokens JWT Expirados**
Limpia tokens JWT expirados del sistema JWT PURO.

```bash
python manage.py cleanup_tokens
```

**Salida esperada:**
```
✅ JWT PURO: eliminados 5 blacklisted + 12 outstanding tokens expirados
Sistema JWT PURO - No hay sesiones opacas que limpiar
✨ Limpieza completada. Total eliminado: 17 registros
```

### 5. **Gestionar Tokens JWT**
Comandos avanzados para gestión de tokens JWT.

```bash
# Ver estadísticas de tokens
python manage.py manage_jwt_tokens stats

# Ver tokens de un usuario específico
python manage.py manage_jwt_tokens user --email admin@test.upeu.edu.pe

# Invalidar todos los tokens de un usuario
python manage.py manage_jwt_tokens revoke --email admin@test.upeu.edu.pe

# Limpiar tokens expirados
python manage.py manage_jwt_tokens cleanup
```

### 6. **Debug de Sesiones JWT**
Muestra información detallada de tokens JWT activos.

```bash
python manage.py debug_sessions
```

**Salida esperada:**
```
🔍 Debug de Tokens JWT Activos
📊 Estadísticas de Tokens JWT:
  • Total tokens: 6
  • Tokens activos: 6
  • Tokens blacklisted: 0
  • Tokens expirados: 1

🕐 Últimos 10 tokens:
  ✅ admin@test.upeu.edu.pe - 2025-10-09 22:44:07
  ✅ coordinador@test.upeu.edu.pe - 2025-10-09 21:30:15
```

## 🔄 Flujo Completo de Configuración

### Paso 1: Aplicar migraciones
```bash
python manage.py migrate
```

### Paso 2: Inicializar permisos y roles
```bash
python manage.py init_permissions
```

### Paso 3: Crear usuarios de prueba
```bash
python manage.py create_test_users
```

### Paso 4: (Opcional) Migrar usuarios existentes
```bash
python manage.py migrate_user_roles --dry-run
python manage.py migrate_user_roles
```

## 📊 Campos en el Modelo User

### Campo `role` (Legacy - mantener por compatibilidad)
- **Tipo**: `CharField`
- **Valores**: 'PRACTICANTE', 'SUPERVISOR', 'COORDINADOR', 'SECRETARIA', 'ADMINISTRADOR'
- **Estado**: Deprecado pero funcional
- **Uso**: Solo para compatibilidad con código antiguo

### Campo `role_obj` (Nuevo Sistema)
- **Tipo**: `ForeignKey` → `Role`
- **Valor**: Referencia al objeto Role completo
- **Estado**: Sistema actual
- **Uso**: Gestión de roles y permisos

### ¿Qué hacer con usuarios antiguos?

#### Opción 1: Migrar automáticamente (Recomendado)
```bash
python manage.py migrate_user_roles
```

#### Opción 2: Migrar manualmente en Django shell
```python
from django.contrib.auth import get_user_model
from src.adapters.secondary.database.models import Role

User = get_user_model()

# Ver usuarios sin role_obj
users = User.objects.filter(role_obj__isnull=True)
for user in users:
    print(f"{user.email} - role={user.role}, role_obj={user.role_obj}")

# Migrar uno por uno
user = User.objects.get(email='ejemplo@upeu.edu.pe')
role = Role.objects.get(code=user.role)
user.role_obj = role
user.save()
```

#### Opción 3: Eliminar usuarios de prueba antiguos
```bash
# En Django shell
python manage.py shell

# Eliminar usuarios específicos
from django.contrib.auth import get_user_model
User = get_user_model()

# Ver todos los usuarios
User.objects.all().values('email', 'role', 'role_obj')

# Eliminar usuarios de prueba sin role_obj
User.objects.filter(email__contains='@test.upeu.edu.pe', role_obj__isnull=True).delete()
```

## ⚠️ Importante

1. **NO borres el campo `role`** - Se mantiene por compatibilidad
2. **El sistema usa `role_obj`** - Es el campo activo del nuevo sistema
3. **Ambos campos coexisten** - `role` es backup, `role_obj` es principal
4. **Los permisos se calculan desde `role_obj`** - No desde `role`

## 🔐 Verificación de Cuenta Inactiva

Cuando un usuario con cuenta inactiva intenta hacer login, recibe este mensaje:

```
❌ Tu cuenta está inactiva. Contacta al administrador para reactivarla.
```

Para reactivar una cuenta:

### GraphQL (ADMIN)
```graphql
mutation {
  updateUser(id: "user-uuid", input: { isActive: true }) {
    success
    message
  }
}
```

### Django Shell
```python
from django.contrib.auth import get_user_model
User = get_user_model()

user = User.objects.get(email='ejemplo@upeu.edu.pe')
user.is_active = True
user.save()
```

### Django Admin
```
1. Ir a /admin/database/user/
2. Seleccionar usuario
3. Marcar checkbox "Activo"
4. Guardar
```

## 🎯 Resumen

| Comando | Propósito | Cuándo usar |
|---------|-----------|-------------|
| `init_permissions` | Crear permisos y roles | Una vez al inicio |
| `migrate_user_roles` | Migrar usuarios legacy | Después de init_permissions |
| `create_users` | Crear usuarios de prueba | Para testing/desarrollo |
| `cleanup_tokens` | Limpiar tokens JWT expirados | Periódicamente (cron job) |
| `manage_jwt_tokens` | Gestión avanzada JWT | Administración de tokens |
| `debug_sessions` | Debug de tokens activos | Troubleshooting JWT |
