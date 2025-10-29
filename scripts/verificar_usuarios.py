"""
Script para verificar usuarios en la BD y crear uno si no existe.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def verificar_usuarios():
    print("=" * 80)
    print("🔍 VERIFICANDO USUARIOS EN LA BASE DE DATOS")
    print("=" * 80)
    
    # Listar todos los usuarios
    usuarios = User.objects.all()
    total = usuarios.count()
    
    print(f"\n📊 Total de usuarios: {total}")
    
    if total == 0:
        print("\n❌ NO HAY USUARIOS EN LA BASE DE DATOS")
        print("\n💡 Opciones:")
        print("1. Ejecuta: python manage.py createsuperuser")
        print("2. O este script creará uno automáticamente")
        
        crear = input("\n¿Crear usuario automáticamente? (s/n): ")
        if crear.lower() == 's':
            crear_usuario_test()
        return
    
    print("\n👥 Usuarios existentes:\n")
    for user in usuarios:
        print(f"📧 Email: {user.correo}")
        print(f"   ID: {user.id}")
        print(f"   Nombres: {user.nombres} {user.apellidos}")
        print(f"   DNI: {user.dni}")
        print(f"   Rol: {user.rol_id.nombre if user.rol_id else 'Sin rol'}")
        print(f"   ✅ Activo: {user.activo}")
        print(f"   🔧 Staff: {user.is_staff}")
        print(f"   👑 Superuser: {user.is_superuser}")
        print("-" * 80)

def crear_usuario_test():
    print("\n" + "=" * 80)
    print("🆕 CREANDO USUARIO DE PRUEBA")
    print("=" * 80)
    
    email = "admin@upeu.edu.pe"
    password = "admin123"
    
    # Verificar si ya existe
    if User.objects.filter(correo=email).exists():
        print(f"\n⚠️ El usuario {email} ya existe")
        user = User.objects.get(correo=email)
        
        if not user.activo:
            print("❌ Usuario INACTIVO - Activando...")
            user.activo = True
            user.save()
            print("✅ Usuario activado")
        
        # Cambiar contraseña
        print(f"\n🔑 Actualizando contraseña a: {password}")
        user.set_password(password)
        user.save()
        print("✅ Contraseña actualizada")
        
    else:
        print(f"\n📧 Email: {email}")
        print(f"🔑 Password: {password}")
        
        user = User.objects.create_superuser(
            correo=email,
            nombres="Admin",
            apellidos="Sistema",
            dni="12345678",
            password=password
        )
        print("\n✅ Usuario creado exitosamente!")
    
    print("\n" + "=" * 80)
    print("📋 CREDENCIALES PARA LOGIN:")
    print("=" * 80)
    print(f"Email: {email}")
    print(f"Password: {password}")
    print("\n💡 Úsalas en Postman:")
    print(f'POST http://localhost:8000/api/v1/auth/login/')
    print(f'Body: {{"email": "{email}", "password": "{password}"}}')

if __name__ == "__main__":
    verificar_usuarios()
