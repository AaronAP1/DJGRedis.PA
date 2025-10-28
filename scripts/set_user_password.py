"""
Script para establecer contraseña de un usuario.
Uso: python scripts/set_user_password.py <email> <nueva_contraseña>
"""
import sys
import os
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from src.adapters.secondary.database.models import User


def set_password(email, password):
    """Establece la contraseña de un usuario."""
    try:
        user = User.objects.get(correo=email)
        user.set_password(password)
        user.save()
        print(f"✅ Contraseña actualizada correctamente para {email}")
        print(f"   Puedes hacer login en http://localhost:8000/admin/")
        print(f"   Usuario: {email}")
        print(f"   Contraseña: {password}")
    except User.DoesNotExist:
        print(f"❌ Error: No existe usuario con correo {email}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Uso: python scripts/set_user_password.py <email> <contraseña>")
        print("Ejemplo: python scripts/set_user_password.py admin@upeu.edu.pe MiContra123!")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    set_password(email, password)
