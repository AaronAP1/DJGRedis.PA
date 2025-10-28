# 📚 Guía de Uso de Swagger UI con JWT

## 🔐 ¿Cómo Autenticarse en Swagger?

### Paso 1: Obtener tu Token JWT

Tienes **dos opciones** para obtener un token:

#### Opción A: Login desde Swagger UI
1. Ve a `/api/docs/` (Swagger UI)
2. Busca el endpoint `POST /api/v2/auth/jwt/login/`
3. Haz click en "Try it out"
4. Ingresa tus credenciales:
```json
{
  "email": "admin@upeu.edu.pe",
  "password": "Admin123!"
}
```
5. Click en "Execute"
6. **COPIA** el `access_token` de la respuesta

#### Opción B: Login desde Terminal
```bash
# PowerShell
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v2/auth/jwt/login/" -Method POST -Body (@{email="admin@upeu.edu.pe"; password="Admin123!"} | ConvertTo-Json) -ContentType "application/json"
$response.data.access_token
```

### Paso 2: Configurar la Autenticación en Swagger

1. **Busca el botón "Authorize" 🔓** en la parte superior derecha de Swagger UI
2. **Haz click** en el botón "Authorize"
3. Se abrirá un modal con el campo **"Bearer (http, Bearer)"**
4. **Pega tu token** en el campo `Value:` con el formato:
   ```
   Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
   ```
   
   ⚠️ **IMPORTANTE**: Debe incluir la palabra `Bearer` seguida de un espacio y luego el token

5. Click en **"Authorize"**
6. Click en **"Close"**

### Paso 3: Usar los Endpoints

Ahora todos los endpoints que requieren autenticación funcionarán correctamente:

- ✅ El candado cerrado 🔒 aparecerá en cada endpoint
- ✅ El header `Authorization: Bearer <token>` se enviará automáticamente
- ✅ Podrás ejecutar cualquier endpoint según tus permisos

---

## 👥 Roles y Permisos

### SUPERADMIN / ADMINISTRADOR
**¿Qué puede hacer?**
- ✅ **TODOS** los endpoints del sistema
- ✅ Crear, editar, eliminar usuarios
- ✅ Gestionar empresas, estudiantes, prácticas
- ✅ Acceder a dashboards y reportes
- ✅ Configurar el sistema

**Endpoints principales:**
- `GET/POST/PUT/DELETE /api/v2/users/`
- `GET/POST/PUT/DELETE /api/v2/empresas/`
- `GET/POST/PUT/DELETE /api/v2/estudiantes/`
- `GET/POST/PUT/DELETE /api/v2/practicas/`
- `GET /api/v2/dashboards/*`
- `GET /api/v2/reportes/*`

---

### COORDINADOR
**¿Qué puede hacer?**
- ✅ Ver todos los estudiantes y prácticas
- ✅ Aprobar/rechazar prácticas
- ✅ Asignar supervisores
- ✅ Generar reportes académicos
- ✅ Gestionar convenios

**Endpoints principales:**
- `GET /api/v2/estudiantes/`
- `GET /api/v2/practicas/`
- `POST /api/v2/practicas/{id}/aprobar/`
- `POST /api/v2/practicas/{id}/rechazar/`
- `GET /api/v2/dashboards/coordinador/`

---

### SECRETARIA
**¿Qué puede hacer?**
- ✅ Ver estudiantes y empresas
- ✅ Registrar nuevas empresas
- ✅ Ver documentos de prácticas
- ✅ Generar cartas de presentación
- ❌ NO puede aprobar prácticas

**Endpoints principales:**
- `GET /api/v2/estudiantes/`
- `GET /api/v2/empresas/`
- `POST /api/v2/empresas/`
- `GET /api/v2/documentos/`
- `GET /api/v2/dashboards/secretaria/`

---

### SUPERVISOR (Empresa)
**¿Qué puede hacer?**
- ✅ Ver sus practicantes asignados
- ✅ Evaluar practicantes
- ✅ Registrar asistencias
- ✅ Generar informes de evaluación
- ❌ NO puede ver otros practicantes

**Endpoints principales:**
- `GET /api/v2/practicas/mis-practicantes/`
- `POST /api/v2/evaluaciones/`
- `POST /api/v2/asistencias/`
- `GET /api/v2/dashboards/supervisor/`

---

### PRACTICANTE (Estudiante)
**¿Qué puede hacer?**
- ✅ Ver su propia práctica
- ✅ Subir documentos
- ✅ Registrar actividades diarias
- ✅ Ver su evaluación
- ❌ NO puede ver otras prácticas

**Endpoints principales:**
- `GET /api/v2/practicas/mis-practicas/`
- `POST /api/v2/documentos/`
- `POST /api/v2/actividades/`
- `GET /api/v2/evaluaciones/mis-evaluaciones/`

---

## 🔧 Solución de Problemas

### ❌ Error 401: "Las credenciales de autenticación no se proveyeron"

**Causas comunes:**
1. **No autorizaste** en Swagger (botón "Authorize")
2. **Token expirado** (los access tokens duran 15 minutos por defecto)
3. **Formato incorrecto** del token (debe ser `Bearer <token>`)
4. **Token inválido** o corrupto

**Solución:**
1. Obtén un nuevo token haciendo login nuevamente
2. Autoriza en Swagger con el nuevo token
3. Intenta el endpoint nuevamente

---

### ❌ Error 403: "No tienes permiso para realizar esta acción"

**Causa:**
Tu rol no tiene permisos para ese endpoint específico.

**Ejemplo:**
- Un **PRACTICANTE** no puede acceder a `GET /api/v2/users/`
- Un **SUPERVISOR** no puede aprobar prácticas

**Solución:**
- Usa un usuario con el rol adecuado
- Revisa la tabla de permisos arriba

---

### ❌ Error 400: "Token inválido o expirado"

**Causa:**
El access token expiró (duración: 15 minutos).

**Solución:**
Usa el refresh token para obtener uno nuevo:

```bash
# Endpoint de refresh
POST /api/v2/auth/jwt/refresh/

# Body (si tienes el refresh_token)
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

O simplemente haz login nuevamente.

---

## 📋 Checklist para Probar un Endpoint

- [ ] ¿Obtuve el token JWT?
- [ ] ¿Autoricé en Swagger con el botón "Authorize"?
- [ ] ¿El formato del token es correcto? (`Bearer <token>`)
- [ ] ¿Mi rol tiene permisos para este endpoint?
- [ ] ¿El token está vigente? (no expirado)

---

## 🎯 Ejemplos Prácticos

### Ejemplo 1: Listar Estudiantes como ADMINISTRADOR

```
1. Login:
   POST /api/v2/auth/jwt/login/
   Body: {"email": "admin@upeu.edu.pe", "password": "Admin123!"}
   
2. Copiar access_token de la respuesta

3. Authorize en Swagger:
   Value: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
   
4. Probar endpoint:
   GET /api/v2/estudiantes/
   ✅ Debería funcionar
```

### Ejemplo 2: Ver Mis Prácticas como PRACTICANTE

```
1. Login con estudiante:
   POST /api/v2/auth/jwt/login/
   Body: {"email": "estudiante@upeu.edu.pe", "password": "Estudiante123!"}
   
2. Copiar access_token

3. Authorize en Swagger

4. Probar endpoint:
   GET /api/v2/practicas/mis-practicas/
   ✅ Debería funcionar
   
5. Intentar ver todas las prácticas:
   GET /api/v2/practicas/
   ❌ Error 403: No tienes permiso (correcto, un estudiante no puede ver todas)
```

---

## 🔄 Flujo Completo de Autenticación

```
┌─────────────────────────────────────────────────────────┐
│ 1. Usuario ingresa credenciales en /api/v2/auth/login/ │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Sistema valida y genera JWT tokens                  │
│    - access_token (15 min)                              │
│    - refresh_token (5 días)                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Usuario autoriza en Swagger con access_token        │
│    Format: Bearer <access_token>                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 4. Cada request incluye header:                         │
│    Authorization: Bearer <access_token>                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 5. DRF valida token y verifica permisos                │
│    - ✅ Token válido + Permisos OK → 200 OK            │
│    - ❌ Token inválido → 401 Unauthorized              │
│    - ❌ Sin permisos → 403 Forbidden                   │
└─────────────────────────────────────────────────────────┘
```

---

## 📌 Información Adicional

- **URL Swagger UI**: http://localhost:8000/api/docs/
- **URL ReDoc**: http://localhost:8000/api/redoc/
- **URL Schema JSON**: http://localhost:8000/api/schema/

- **Duración Access Token**: 15 minutos (configurable en `.env`)
- **Duración Refresh Token**: 5 días (configurable en `.env`)

---

## 🆘 ¿Necesitas Ayuda?

Si sigues teniendo problemas:

1. Verifica que el servidor esté corriendo: `python manage.py runserver`
2. Revisa los logs en la consola del servidor
3. Asegúrate de que tu usuario esté activo en la base de datos
4. Verifica que el rol del usuario sea correcto
