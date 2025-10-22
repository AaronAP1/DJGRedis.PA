# 🔐 Autenticación JWT PURO

## 📋 Descripción

Este sistema implementa autenticación completamente basada en JWT con cookies HttpOnly y protección Cloudflare Turnstile. Utiliza únicamente tokens JWT con cookies HttpOnly.

## 🏗️ Arquitectura

```
┌─────────────────┐    JWT Cookies    ┌──────────────────┐
{{ ... }}
│   Frontend      │◄─────────────────►│    Backend       │
│   (Angular)     │   HttpOnly        │   (Django JWT)   │
└─────────────────┘                   └──────────────────┘
                                               │
                                               ▼
                                      ┌──────────────────┐
                                      │   PostgreSQL     │
                                      │                  │
                                      │ ├─token_blacklist│
                                      │ └─outstanding    │
                                      └──────────────────┘
```

## ⚙️ Configuración

### JWT Settings
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),   # 15 minutos
    'REFRESH_TOKEN_LIFETIME': timedelta(days=5),      # 5 días
    'ROTATE_REFRESH_TOKENS': True,                    # Rotar por seguridad
    'BLACKLIST_AFTER_ROTATION': True,                 # Blacklist rotados
    'UPDATE_LAST_LOGIN': True,
}
```

### Cookies Configuration
```python
# Access Token Cookie
ACCESS_COOKIE_NAME = 'access_token'
ACCESS_COOKIE_PATH = '/api/v1/'
ACCESS_COOKIE_MAX_AGE = 60 * 15  # 15 minutos

# Refresh Token Cookie
REFRESH_COOKIE_NAME = 'refresh_token'
REFRESH_COOKIE_PATH = '/api/v1/'
REFRESH_COOKIE_MAX_AGE = 60 * 60 * 24 * 5  # 5 días
```

## 🍪 Cookies en DevTools

```
Application → Cookies:
├── access_token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9... (HttpOnly, 15 min)
├── refresh_token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9... (HttpOnly, 5 días)
├── csrftoken: abc123... (Legible, CSRF protection)
└── sessionid: def456... (Django admin)
```

## 🔄 Flujo de Autenticación

### 1. Login
```graphql
mutation {
  jwtLogin(email: "user@example.com", password: "password") {
    success
    message
    user {
      id
      email
      nombreCompleto
    }
  }
}
```

**Resultado:**
- ✅ Crea access token (15 min)
- ✅ Crea refresh token (5 días)
- ✅ Establece cookies HttpOnly
- ✅ Actualiza last_login

### 2. Requests Autenticados
```
GET /api/v1/users/me/
Cookie: access_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Proceso:**
1. Middleware extrae access token de cookie
2. Valida token JWT
3. Obtiene usuario del token
4. Establece request.user

### 3. Refresh Tokens
```graphql
mutation {
  jwtRefresh {
    success
    message
  }
}
```

**Resultado:**
- ✅ Valida refresh token
- ✅ Genera nuevo access token
- ✅ Opcionalmente rota refresh token
- ✅ Actualiza cookies

### 4. Logout
```graphql
mutation {
  jwtLogout(logoutAll: false) {
    success
    message
  }
}
```

**Resultado:**
- ✅ Agrega refresh token a blacklist
- ✅ Limpia cookies JWT
- ✅ Invalida sesión

## 🛠️ Comandos de Gestión

### Debug de Tokens
```bash
# Ver estadísticas generales
python manage.py debug_sessions

# Ver tokens de usuario específico
python manage.py debug_sessions --user-email admin@test.upeu.edu.pe

# Limpiar todos los tokens (blacklist)
python manage.py debug_sessions --clear-all
```

### Gestión de Tokens
```bash
# Limpiar tokens expirados
python manage.py manage_jwt_tokens cleanup

# Listar tokens activos
python manage.py manage_jwt_tokens list

# Estadísticas (últimos 7 días)
python manage.py manage_jwt_tokens stats --days 7

# Blacklist tokens de usuario
python manage.py manage_jwt_tokens blacklist_user --user-email user@example.com

# Blacklist TODOS los tokens (emergencia)
python manage.py manage_jwt_tokens blacklist_all --force
```

## 🔒 Seguridad

### Características de Seguridad
- ✅ **HttpOnly Cookies**: Inmune a XSS
- ✅ **Token Rotation**: Refresh tokens se rotan
- ✅ **Blacklist**: Tokens inválidos van a blacklist
- ✅ **Expiración**: Access tokens de corta duración
- ✅ **CSRF Protection**: Token CSRF separado
- ✅ **Secure Cookies**: En producción con HTTPS

### Middleware Stack
```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'src.infrastructure.middleware.jwt_auth.JWTAuthenticationMiddleware',  # JWT Auth
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
    'src.infrastructure.middleware.rate_limit.RateLimitMiddleware',
    'src.infrastructure.middleware.security.SecurityMiddleware',
    'src.infrastructure.middleware.jwt_auth.JWTCookieMiddleware',  # JWT Cookies
]
```

## 📊 Monitoreo

### Logs de Seguridad
```python
# Login exitoso
security_event_logger.log_security_event(
    'jwt_session_created',
    f"New JWT session created for user {user.email}",
    user_id=str(user.id)
)

# Login fallido
security_event_logger.log_security_event(
    'login_failed',
    f"Failed login attempt for email: {email}",
    severity='WARNING'
)

# Logout
security_event_logger.log_security_event(
    'jwt_session_logout',
    f"JWT session logout for user_id {user_id}",
    user_id=str(user_id)
)
```

### Métricas Importantes
- **Tokens activos**: Número de tokens no blacklisted
- **Tokens expirados**: Tokens que deben limpiarse
- **Rotaciones**: Frecuencia de refresh
- **Blacklist size**: Tamaño de la blacklist

## 🧪 Testing

### Quickstart GraphQL
1. Ir a: `http://localhost:8000/graphql/quickstart/`
2. **Login JWT**: Clic en "Login JWT"
3. **Ver Perfil**: Clic en "Ver Mi Perfil"
4. **Refresh**: Clic en "Refresh JWT"
5. **Logout**: Clic en "Logout JWT"

### Verificar Cookies
1. DevTools → Application → Cookies
2. Verificar `access_token` y `refresh_token`
3. Ambas deben ser HttpOnly
4. Path correcto: `/api/v1/`

### Verificar Expiración
1. Esperar 15 minutos (access token expira)
2. Hacer request → Debería fallar
3. Hacer refresh → Debería funcionar
4. Esperar 5 días → Logout automático

## 🚨 Troubleshooting

### Token no válido
```bash
# Verificar tokens en BD
python manage.py manage_jwt_tokens list

# Limpiar tokens problemáticos
python manage.py manage_jwt_tokens cleanup
```

### Cookies no se establecen
1. Verificar `CORS_ALLOW_CREDENTIALS = True`
2. Verificar `CSRF_TRUSTED_ORIGINS`
3. Verificar middleware order

### Logout no funciona
1. Verificar que refresh token existe
2. Verificar que no está ya en blacklist
3. Verificar cookies path

## 📈 Rendimiento

### Optimizaciones
- Tokens JWT son stateless (no consultas BD por request)
- Blacklist se consulta solo en refresh/logout
- Cleanup automático de tokens expirados
- Índices en tablas de blacklist

### Escalabilidad
- JWT permite múltiples instancias sin sesiones compartidas
- Blacklist puede moverse a Redis si es necesario
- Tokens pueden incluir permisos para reducir consultas

## 🔄 Migración desde Sistema Anterior

### Pasos Realizados
1. ✅ Eliminados modelos `OpaqueSession`
2. ✅ Eliminados middleware opaco
3. ✅ Creado `JWTAuthenticationService`
4. ✅ Creado middleware JWT
5. ✅ Actualizadas mutations GraphQL
6. ✅ Actualizada configuración
7. ✅ Actualizado quickstart

### Verificación Post-Migración
```bash
# Verificar que no hay archivos opaque
find . -name "*opaque*" -type f

# Verificar que no hay referencias en código
grep -r "OpaqueSession" src/
grep -r "SessionActivity" src/

# Verificar JWT funciona
python manage.py debug_sessions

# Aplicar migración para eliminar tablas
python manage.py migrate
```

---

**Sistema JWT PURO completamente funcional** 🚀
