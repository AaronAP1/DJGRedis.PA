# Cloudflare Turnstile - Sistema JWT PURO

## 🛡️ Configuración de Cloudflare Turnstile

### ¿Qué es Cloudflare Turnstile?
Cloudflare Turnstile es el reemplazo moderno de reCAPTCHA que ofrece:
- ✅ **Mejor UX**: Sin puzzles molestos
- ✅ **Más privacidad**: No rastrea usuarios
- ✅ **Mejor rendimiento**: Más rápido que reCAPTCHA
- ✅ **Gratis**: Sin límites para sitios web

### Configuración en Cloudflare Dashboard

1. **Ir a Cloudflare Dashboard**
   ```
   https://dash.cloudflare.com/
   ```

2. **Crear Site Key**
   - Ir a "Turnstile" en el sidebar
   - Clic en "Add Site"
   - Configurar:
     - **Site name**: DJGRedis.PA
     - **Domain**: tu-dominio.com (o localhost para desarrollo)
     - **Widget mode**: Managed (recomendado)

3. **Obtener Keys**
   ```
   Site Key: 0x4AAAAAAA... (público - va en frontend)
   Secret Key: 0x4AAAAAAA... (privado - va en backend)
   ```

## ⚙️ Configuración en Django

### 1. Variables de Entorno
Agregar en `.env`:
```bash
# Cloudflare Turnstile
CLOUDFLARE_TURNSTILE_SITE_KEY=0x4AAAAAAA...
CLOUDFLARE_TURNSTILE_SECRET_KEY=0x4AAAAAAA...
CLOUDFLARE_TURNSTILE_ENABLED=True
```

### 2. Settings.py
```python
# Cloudflare Turnstile
CLOUDFLARE_TURNSTILE_SITE_KEY = config('CLOUDFLARE_TURNSTILE_SITE_KEY', default='')
CLOUDFLARE_TURNSTILE_SECRET_KEY = config('CLOUDFLARE_TURNSTILE_SECRET_KEY', default='')
CLOUDFLARE_TURNSTILE_ENABLED = config('CLOUDFLARE_TURNSTILE_ENABLED', default=False, cast=bool)
```

### 3. Servicio de Verificación
```python
# src/infrastructure/security/cloudflare_turnstile.py
import requests
from django.conf import settings

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

def verify_turnstile_token(token, ip_address=None):
    """Verifica token de Cloudflare Turnstile."""
    if not settings.CLOUDFLARE_TURNSTILE_ENABLED:
        return True  # Bypass en desarrollo
    
    if not token:
        return False
    
    data = {
        'secret': settings.CLOUDFLARE_TURNSTILE_SECRET_KEY,
        'response': token,
    }
    
    if ip_address:
        data['remoteip'] = ip_address
    
    try:
        response = requests.post(VERIFY_URL, data=data, timeout=10)
        result = response.json()
        return result.get('success', False)
    except Exception:
        return False
```

## 🔧 Implementación en GraphQL

### Mutations Actualizadas
```python
# JWT Login con Cloudflare
class JWTLogin(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        cloudflare_token = graphene.String(required=False)
    
    def mutate(self, info, email, password, cloudflare_token=None):
        # Verificar Cloudflare Turnstile
        if not verify_turnstile_token(cloudflare_token, get_client_ip(info.context)):
            return JWTLoginResult(
                success=False,
                message="Verificación de seguridad fallida"
            )
        
        # Continuar con login JWT...
```

## 🌐 Frontend Implementation

### HTML Template
```html
<!-- Cloudflare Turnstile Widget -->
<div class="cf-turnstile" 
     data-sitekey="0x4AAAAAAA..." 
     data-callback="onTurnstileCallback">
</div>

<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
```

### JavaScript
```javascript
function onTurnstileCallback(token) {
    // Token recibido de Cloudflare
    document.getElementById('cloudflareToken').value = token;
}

// Usar en login
const loginMutation = `
  mutation JWTLogin($email: String!, $password: String!, $cloudflareToken: String!) {
    jwtLogin(email: $email, password: $password, cloudflareToken: $cloudflareToken) {
      success
      message
      user { id email username }
    }
  }
`;
```

## 🚀 Quickstart Actualizado

### Uso en GraphiQL
```graphql
mutation {
  jwtLogin(
    email: "admin@test.upeu.edu.pe"
    password: "Admin123!"
    cloudflareToken: "0.AQAAAAAAA..."
  ) {
    success
    message
    user {
      id
      email
      username
      role
    }
  }
}
```

## 🔍 Testing y Debug

### Modo Desarrollo
```python
# En settings.py para desarrollo local
CLOUDFLARE_TURNSTILE_ENABLED = False  # Bypass Turnstile
```

### Tokens de Prueba
Cloudflare provee tokens especiales para testing:
```
Always Pass: 1x00000000000000000000AA
Always Fail: 2x00000000000000000000AB
Already Used: 3x00000000000000000000AC
```

### Verificación Manual
```bash
curl -X POST https://challenges.cloudflare.com/turnstile/v0/siteverify \
  -d "secret=YOUR_SECRET_KEY" \
  -d "response=TOKEN_FROM_WIDGET"
```

## 📊 Ventajas vs reCAPTCHA

| Característica | Cloudflare Turnstile | reCAPTCHA |
|---------------|---------------------|-----------|
| **UX** | ✅ Sin puzzles | ❌ Puzzles molestos |
| **Privacidad** | ✅ No tracking | ❌ Google tracking |
| **Rendimiento** | ✅ Más rápido | ❌ Más lento |
| **Costo** | ✅ Gratis ilimitado | ⚠️ Límites gratis |
| **Integración** | ✅ Más simple | ❌ Más complejo |

## 🛠️ Migración desde reCAPTCHA

### Pasos Realizados
1. ✅ Actualizado `quickstart.html` - Cloudflare inputs
2. ✅ Actualizado JavaScript - `cloudflareToken` variables  
3. ✅ Eliminado `recaptcha.html`
4. ✅ Actualizada documentación

### Próximos Pasos
1. Crear servicio de verificación Cloudflare
2. Actualizar mutations GraphQL
3. Configurar variables de entorno
4. Testing en desarrollo

---

**Sistema JWT PURO + Cloudflare Turnstile = Seguridad moderna sin fricción** 🚀
