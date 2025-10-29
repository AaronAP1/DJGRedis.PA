"""
Script de prueba para verificar el sistema de autenticación REST con JWT.
Ejecutar: python scripts/test_rest_login.py
"""

import requests
import json
from pprint import pprint

# Configuración
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/login/"    # ✅ IMPORTANTE: Con slash final
ME_URL = f"{BASE_URL}/api/v1/auth/me/"
USERS_URL = f"{BASE_URL}/api/v2/users/"

# ⚠️ INSTRUCCIONES: Cambia estas credenciales por las tuyas
CREDENTIALS = {
    "email": "admin@upeu.edu.pe",  # Cambiar por tu email real
    "password": "tu_password"       # Cambiar por tu contraseña real
}

def test_login():
    """Prueba el endpoint de login."""
    print("=" * 80)
    print("🔐 PRUEBA 1: LOGIN")
    print("=" * 80)
    
    print(f"\n📍 POST {LOGIN_URL}")
    print(f"📦 Body: {json.dumps(CREDENTIALS, indent=2)}")
    
    response = requests.post(LOGIN_URL, json=CREDENTIALS)
    
    print(f"\n📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ LOGIN EXITOSO!")
        print("\n👤 Usuario:")
        pprint(data.get('user', {}))
        
        access_token = data.get('access')
        refresh_token = data.get('refresh')
        
        print(f"\n🔑 Access Token: {access_token[:50]}...")
        print(f"🔄 Refresh Token: {refresh_token[:50]}...")
        
        return access_token, refresh_token
    else:
        print("\n❌ LOGIN FALLIDO!")
        print(f"Error: {response.text}")
        return None, None


def test_me(access_token):
    """Prueba el endpoint /me/ con el token."""
    print("\n" + "=" * 80)
    print("👤 PRUEBA 2: OBTENER PERFIL (ME)")
    print("=" * 80)
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    print(f"\n📍 GET {ME_URL}")
    print(f"🔑 Authorization: Bearer {access_token[:30]}...")
    
    response = requests.get(ME_URL, headers=headers)
    
    print(f"\n📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ PERFIL OBTENIDO!")
        print("\n📋 Datos del usuario:")
        pprint(data)
    else:
        print("\n❌ ERROR AL OBTENER PERFIL!")
        print(f"Error: {response.text}")


def test_protected_endpoint(access_token):
    """Prueba un endpoint protegido (lista de usuarios)."""
    print("\n" + "=" * 80)
    print("🔒 PRUEBA 3: ENDPOINT PROTEGIDO (Lista de Usuarios)")
    print("=" * 80)
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    print(f"\n📍 GET {USERS_URL}")
    print(f"🔑 Authorization: Bearer {access_token[:30]}...")
    
    response = requests.get(USERS_URL, headers=headers)
    
    print(f"\n📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ ACCESO AUTORIZADO!")
        print(f"\n📊 Total de usuarios: {data.get('count', 0)}")
        
        if data.get('results'):
            print("\n👥 Primeros usuarios:")
            for user in data['results'][:3]:
                print(f"  - {user.get('full_name')} ({user.get('email')}) - {user.get('role')}")
    elif response.status_code == 403:
        print("\n⛔ ACCESO DENEGADO!")
        print("Tu rol no tiene permisos para ver usuarios.")
        print(response.text)
    else:
        print("\n❌ ERROR!")
        print(f"Error: {response.text}")


def test_without_token():
    """Prueba acceso sin token."""
    print("\n" + "=" * 80)
    print("🚫 PRUEBA 4: ACCESO SIN TOKEN (debe fallar)")
    print("=" * 80)
    
    print(f"\n📍 GET {USERS_URL}")
    print("🔑 Sin Authorization header")
    
    response = requests.get(USERS_URL)
    
    print(f"\n📊 Status Code: {response.status_code}")
    
    if response.status_code == 401:
        print("\n✅ CORRECTO! Acceso denegado sin token")
    else:
        print("\n⚠️ INESPERADO! Debería rechazar sin token")
    
    print(f"Response: {response.text}")


def main():
    """Ejecuta todas las pruebas."""
    print("\n" + "🚀" * 40)
    print("PRUEBA DEL SISTEMA DE AUTENTICACIÓN REST + JWT")
    print("🚀" * 40)
    
    # Prueba 1: Login
    access_token, refresh_token = test_login()
    
    if not access_token:
        print("\n❌ No se pudo obtener el token. Verifica las credenciales.")
        print("\n💡 INSTRUCCIONES:")
        print("1. Edita este archivo y cambia las credenciales en CREDENTIALS")
        print("2. Asegúrate de tener un usuario creado con:")
        print("   python manage.py createsuperuser")
        print("3. El servidor debe estar corriendo en http://localhost:8000")
        return
    
    # Prueba 2: Me
    test_me(access_token)
    
    # Prueba 3: Endpoint protegido
    test_protected_endpoint(access_token)
    
    # Prueba 4: Sin token
    test_without_token()
    
    print("\n" + "=" * 80)
    print("✅ PRUEBAS COMPLETADAS!")
    print("=" * 80)
    
    print("\n📝 SIGUIENTE PASO: Usar estos datos en Postman")
    print(f"\n🔑 Access Token para copiar en Postman:")
    print(f"{access_token}")
    print(f"\n🔄 Refresh Token:")
    print(f"{refresh_token}")
    
    print("\n💡 En Postman:")
    print("1. Ve a Authorization → Type: Bearer Token")
    print("2. Pega el Access Token")
    print("3. Ya puedes hacer requests a todos los endpoints")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: No se pudo conectar al servidor")
        print("\n💡 Asegúrate de que el servidor esté corriendo:")
        print("   python manage.py runserver")
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {str(e)}")
        import traceback
        traceback.print_exc()
