"""
Demo simple para visualizar modelos C4 - Sistema de Gestión de Prácticas.
Ejecuta un servidor Django simplificado en puerto 8001.
"""

import os
import sys
import django
from pathlib import Path

# Agregar el directorio del proyecto al path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

def setup_django():
    """Configura Django con SQLite para la demostración."""
    
    from django.conf import settings
    
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            SECRET_KEY='demo-c4-models-key',
            
            # Usar SQLite en lugar de PostgreSQL
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',  # Base de datos en memoria
                }
            },
            
            # Apps mínimas
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.staticfiles',
                'rest_framework',
            ],
            
            # Middleware mínimo
            MIDDLEWARE=[
                'django.middleware.security.SecurityMiddleware',
                'django.middleware.common.CommonMiddleware',
                'django.middleware.csrf.CsrfViewMiddleware',
            ],
            
            # REST Framework sin autenticación
            REST_FRAMEWORK={
                'DEFAULT_PERMISSION_CLASSES': [],
                'DEFAULT_AUTHENTICATION_CLASSES': [],
            },
            
            # Templates
            TEMPLATES=[
                {
                    'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    'DIRS': [BASE_DIR / 'templates'],
                    'APP_DIRS': True,
                    'OPTIONS': {
                        'context_processors': [
                            'django.template.context_processors.debug',
                            'django.template.context_processors.request',
                            'django.template.context_processors.static',
                        ],
                    },
                },
            ],
            
            # Configuraciones básicas
            STATIC_URL='/static/',
            ROOT_URLCONF='config.urls',  # Usar las URLs principales
            USE_TZ=True,
            TIME_ZONE='America/Lima',
            
            # Cache en memoria
            CACHES={
                'default': {
                    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                }
            },
        )
    
    django.setup()

def main():
    """Función principal para ejecutar el servidor de demostración."""
    
    print("🚀 Iniciando demo de modelos C4...")
    print("=" * 60)
    
    # Verificar archivos necesarios
    required_files = [
        'docs/arquitectura/c4_models_sistema_practicas.json',
        'templates/c4/visualizer.html',
        'src/adapters/primary/rest_api/views/c4_views.py'
    ]
    
    missing = [f for f in required_files if not Path(f).exists()]
    if missing:
        print("❌ Faltan archivos necesarios:")
        for f in missing:
            print(f"   - {f}")
        print("\n💡 Ejecuta: python docs/arquitectura/c4_models_generator.py")
        return
    
    # Configurar Django
    setup_django()
    
    print("✅ Configuración completada")
    print("\n📋 URLs disponibles:")
    print("   🏠 Inicio: http://localhost:8001/")
    print("   📊 Visualizador C4: http://localhost:8001/api/v1/c4/")
    print("   📋 Modelos JSON: http://localhost:8001/api/v1/c4/models/")
    print("   � Diagrama contexto: http://localhost:8001/api/v1/c4/diagrams/context/")
    print("   � PlantUML raw: http://localhost:8001/api/v1/c4/diagrams/context/raw/")
    
    print("\n🎯 Ve a: http://localhost:8001/api/v1/c4/")
    print("=" * 60)
    
    try:
        from django.core.management import execute_from_command_line
        sys.argv = ['manage.py', 'runserver', '8001', '--noreload']
        execute_from_command_line(sys.argv)
    except KeyboardInterrupt:
        print("\n\n👋 Demo terminada. ¡Gracias!")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == '__main__':
    main()