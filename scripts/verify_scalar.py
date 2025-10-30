#!/usr/bin/env python
"""
Script para verificar que Scalar UI está correctamente instalado y configurado.
"""

def verify_scalar_installation():
    """Verifica que django-scalar esté instalado."""
    try:
        import django_scalar
        print("✅ django-scalar está instalado")
        print(f"   Versión: {django_scalar.__version__}")
        return True
    except ImportError as e:
        print("❌ Error: django-scalar NO está instalado")
        print(f"   {str(e)}")
        return False

def verify_scalar_view():
    """Verifica que la vista de Scalar esté disponible."""
    try:
        from django_scalar.views import scalar_viewer
        print("✅ scalar_viewer importada correctamente")
        return True
    except ImportError as e:
        print("❌ Error al importar scalar_viewer")
        print(f"   {str(e)}")
        return False

def show_documentation_urls():
    """Muestra las URLs de documentación disponibles."""
    print("\n📚 URLs de Documentación API:")
    print("   🚀 Scalar (Principal):  http://localhost:8000/api/scalar/")
    print("   📖 Swagger UI:          http://localhost:8000/api/docs/")
    print("   📄 ReDoc:               http://localhost:8000/api/redoc/")
    print("   🔧 OpenAPI Schema:      http://localhost:8000/api/schema/")
    print("\n💡 Al abrir http://localhost:8000/ se redirige a Scalar automáticamente")

if __name__ == "__main__":
    print("=" * 60)
    print("Verificación de Scalar UI")
    print("=" * 60)
    
    all_ok = True
    all_ok &= verify_scalar_installation()
    all_ok &= verify_scalar_view()
    
    show_documentation_urls()
    
    print("\n" + "=" * 60)
    if all_ok:
        print("✅ ¡Todo está configurado correctamente!")
        print("   Ejecuta: python manage.py runserver")
        print("   Y abre: http://localhost:8000/")
    else:
        print("❌ Hay problemas con la configuración")
        print("   Ejecuta: pip install drf-spectacular-scalar==0.1.0")
    print("=" * 60)
