# Script para verificar configuración de Swagger JWT
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings

def verificar_swagger_jwt():
    """Verifica la configuración de Swagger y JWT."""
    
    print("=" * 70)
    print("🔍 VERIFICACIÓN DE CONFIGURACIÓN SWAGGER + JWT")
    print("=" * 70)
    
    # 1. Verificar REST_FRAMEWORK
    print("\n1️⃣  Configuración REST Framework:")
    print("-" * 70)
    rest_config = settings.REST_FRAMEWORK
    
    auth_classes = rest_config.get('DEFAULT_AUTHENTICATION_CLASSES', [])
    print(f"   ✅ Authentication Classes:")
    for cls in auth_classes:
        print(f"      - {cls}")
    
    perm_classes = rest_config.get('DEFAULT_PERMISSION_CLASSES', [])
    print(f"\n   ✅ Permission Classes:")
    for cls in perm_classes:
        print(f"      - {cls}")
    
    schema_class = rest_config.get('DEFAULT_SCHEMA_CLASS')
    print(f"\n   ✅ Schema Class: {schema_class}")
    
    # 2. Verificar SPECTACULAR_SETTINGS
    print("\n2️⃣  Configuración drf-spectacular:")
    print("-" * 70)
    spectacular = settings.SPECTACULAR_SETTINGS
    
    print(f"   📚 Title: {spectacular.get('TITLE')}")
    print(f"   📝 Version: {spectacular.get('VERSION')}")
    
    # Verificar seguridad JWT
    security = spectacular.get('SECURITY', [])
    print(f"\n   🔐 Security Schemes:")
    if security:
        for scheme in security:
            print(f"      ✅ {scheme}")
    else:
        print(f"      ❌ No hay esquemas de seguridad configurados!")
    
    components = spectacular.get('COMPONENTS', {})
    security_schemes = components.get('securitySchemes', {})
    print(f"\n   🔒 Security Components:")
    if security_schemes:
        for name, config in security_schemes.items():
            print(f"      ✅ {name}:")
            print(f"         Type: {config.get('type')}")
            print(f"         Scheme: {config.get('scheme')}")
            print(f"         Format: {config.get('bearerFormat')}")
    else:
        print(f"      ❌ No hay componentes de seguridad!")
    
    # 3. Verificar SIMPLE_JWT
    print("\n3️⃣  Configuración Simple JWT:")
    print("-" * 70)
    jwt_config = settings.SIMPLE_JWT
    
    access_lifetime = jwt_config.get('ACCESS_TOKEN_LIFETIME')
    refresh_lifetime = jwt_config.get('REFRESH_TOKEN_LIFETIME')
    
    print(f"   ⏱️  Access Token Lifetime: {access_lifetime}")
    print(f"   ⏱️  Refresh Token Lifetime: {refresh_lifetime}")
    print(f"   🔄 Rotate Refresh Tokens: {jwt_config.get('ROTATE_REFRESH_TOKENS')}")
    print(f"   🔐 Algorithm: {jwt_config.get('ALGORITHM')}")
    
    # 4. URLs de documentación
    print("\n4️⃣  URLs de Documentación:")
    print("-" * 70)
    base_url = "http://localhost:8000"
    print(f"   📄 Schema JSON: {base_url}/api/schema/")
    print(f"   📚 Swagger UI: {base_url}/api/docs/")
    print(f"   📖 ReDoc: {base_url}/api/redoc/")
    
    # 5. Instrucciones
    print("\n5️⃣  Instrucciones de Uso:")
    print("-" * 70)
    print(f"   1. Obtén un token JWT:")
    print(f"      POST {base_url}/api/v2/auth/jwt/login/")
    print(f"      Body: {{'email': 'admin@upeu.edu.pe', 'password': 'Admin123!'}}")
    print()
    print(f"   2. Autoriza en Swagger:")
    print(f"      - Ve a {base_url}/api/docs/")
    print(f"      - Click en el botón 'Authorize' (arriba a la derecha)")
    print(f"      - Ingresa: Bearer <tu_access_token>")
    print(f"      - Click en 'Authorize'")
    print()
    print(f"   3. ¡Listo! Ahora puedes usar todos los endpoints")
    
    # 6. Verificación final
    print("\n6️⃣  Estado de la Configuración:")
    print("-" * 70)
    
    checks = []
    checks.append(("JWTAuthentication en REST_FRAMEWORK", 
                   'rest_framework_simplejwt.authentication.JWTAuthentication' in auth_classes))
    checks.append(("Schema Class configurado", 
                   schema_class == 'drf_spectacular.openapi.AutoSchema'))
    checks.append(("Security Schemes definidos", 
                   len(security_schemes) > 0))
    checks.append(("Bearer auth configurado", 
                   'Bearer' in security_schemes))
    
    all_ok = True
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"   {status} {check_name}")
        if not check_result:
            all_ok = False
    
    print("\n" + "=" * 70)
    if all_ok:
        print("✅ CONFIGURACIÓN CORRECTA - Swagger JWT está listo para usar")
    else:
        print("❌ HAY PROBLEMAS - Revisa la configuración arriba")
    print("=" * 70)
    print()
    
    return all_ok

if __name__ == '__main__':
    verificar_swagger_jwt()
