"""
Script para cambiar contraseña de un usuario existente.
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Usuario a actualizar
EMAIL = "admin@upeu.edu.pe"
NUEVA_PASSWORD = "admin123"

try:
    user = User.objects.get(correo=EMAIL)
    user.set_password(NUEVA_PASSWORD)
    user.save()
    
    print("=" * 80)
    print("✅ CONTRASEÑA ACTUALIZADA EXITOSAMENTE")
    print("=" * 80)
    print(f"\n📧 Email: {EMAIL}")
    print(f"🔑 Nueva Password: {NUEVA_PASSWORD}")
    print(f"\n👤 Usuario: {user.nombres} {user.apellidos}")
    print(f"🎭 Rol: {user.rol_id.nombre if user.rol_id else 'Sin rol'}")
    print(f"✅ Activo: {user.activo}")
    print(f"👑 Superuser: {user.is_superuser}")
    
    print("\n" + "=" * 80)
    print("📋 USA ESTAS CREDENCIALES EN POSTMAN:")
    print("=" * 80)
    print(f'\nPOST http://localhost:8000/api/v1/auth/login/')
    print(f'\nBody (JSON):')
    print(f'{{\n    "email": "{EMAIL}",\n    "password": "{NUEVA_PASSWORD}"\n}}')
    print("\n" + "=" * 80)
    
except User.DoesNotExist:
    print(f"❌ Usuario {EMAIL} no existe")
