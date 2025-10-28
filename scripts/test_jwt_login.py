"""
Script de debugging para probar login JWT.
"""
import sys
import os
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import authenticate
from src.adapters.secondary.database.models import User
from rest_framework_simplejwt.tokens import RefreshToken

def test_login():
    """Test de login básico."""
    print("🔍 Testing JWT Login Process...")
    print()
    
    # Paso 1: Verificar que el usuario existe
    print("1️⃣ Verificando usuario...")
    try:
        user = User.objects.get(correo='pruebas2@gmail.com')
        print(f"   ✅ Usuario encontrado: {user.correo}")
        print(f"   - ID: {user.id}")
        print(f"   - Nombres: {user.nombres}")
        print(f"   - Apellidos: {user.apellidos}")
        print(f"   - Activo: {user.activo}")
        print(f"   - is_active: {user.is_active}")
        print()
    except User.DoesNotExist:
        print("   ❌ Usuario no encontrado")
        return
    
    # Paso 2: Verificar autenticación
    print("2️⃣ Probando autenticación...")
    try:
        auth_user = authenticate(username='pruebas2@gmail.com', password='admin123')
        if auth_user:
            print(f"   ✅ Autenticación exitosa")
            print(f"   - Usuario autenticado: {auth_user.correo}")
        else:
            print("   ❌ Autenticación fallida - credenciales incorrectas")
            # Verificar el hash de la contraseña
            print(f"   - Hash actual: {user.hash_contraseña[:50]}...")
            print(f"   - Verificando contraseña manualmente...")
            if user.check_password('admin123'):
                print("   ✅ check_password() funciona correctamente")
            else:
                print("   ❌ check_password() falla - la contraseña no coincide")
            return
        print()
    except Exception as e:
        print(f"   ❌ Error en autenticación: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Paso 3: Generar tokens JWT
    print("3️⃣ Generando tokens JWT...")
    try:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        print("   ✅ Tokens generados exitosamente")
        print(f"   - Access token: {access_token[:50]}...")
        print(f"   - Refresh token: {refresh_token[:50]}...")
        print(f"   - JTI: {refresh['jti']}")
        print()
    except Exception as e:
        print(f"   ❌ Error generando tokens: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Paso 4: Crear OutstandingToken
    print("4️⃣ Creando OutstandingToken...")
    try:
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
        
        outstanding_token, created = OutstandingToken.objects.get_or_create(
            jti=refresh['jti'],
            defaults={
                'user': user,
                'token': str(refresh),
                'created_at': refresh['iat'],
                'expires_at': refresh['exp'],
            }
        )
        
        if created:
            print("   ✅ OutstandingToken creado")
        else:
            print("   ℹ️  OutstandingToken ya existía")
        
        print(f"   - ID: {outstanding_token.id}")
        print(f"   - User ID: {outstanding_token.user_id}")
        print(f"   - JTI: {outstanding_token.jti}")
        print()
    except Exception as e:
        print(f"   ❌ Error creando OutstandingToken: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("🎉 Proceso de login completado exitosamente!")
    print()
    print("📋 Resumen:")
    print(f"   - Usuario: {user.correo}")
    print(f"   - Access Token: {access_token[:30]}...")
    print(f"   - Refresh Token: {refresh_token[:30]}...")

if __name__ == '__main__':
    test_login()
