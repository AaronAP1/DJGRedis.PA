"""
Script de verificación de la Fase 7 - Dashboard Endpoints.

Verifica que todos los archivos y configuraciones estén correctos.
"""

import os
import sys
from pathlib import Path


def check_file_exists(filepath, description):
    """Verifica que un archivo exista."""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NO ENCONTRADO")
        return False


def check_directory_exists(dirpath, description):
    """Verifica que un directorio exista."""
    if os.path.isdir(dirpath):
        print(f"✅ {description}: {dirpath}")
        return True
    else:
        print(f"❌ {description}: {dirpath} - NO ENCONTRADO")
        return False


def main():
    """Ejecuta las verificaciones."""
    print("="*70)
    print("VERIFICACIÓN DE FASE 7 - DASHBOARD ENDPOINTS")
    print("="*70)
    print()
    
    base_path = Path(__file__).parent.parent
    
    all_ok = True
    
    # Verificar archivos principales
    print("📁 ARCHIVOS PRINCIPALES:")
    print("-"*70)
    
    files_to_check = [
        (base_path / "src/adapters/primary/rest_api/views/dashboards.py", 
         "DashboardViewSet"),
        (base_path / "src/adapters/primary/rest_api/views/reports.py", 
         "ReportsViewSet"),
        (base_path / "src/adapters/primary/rest_api/views/__init__.py", 
         "Views __init__"),
        (base_path / "src/adapters/primary/rest_api/urls_api_v2.py", 
         "URLs API v2 (actualizado)"),
        (base_path / "src/adapters/primary/rest_api/views/README_DASHBOARDS.md", 
         "Documentación Dashboards"),
        (base_path / "src/adapters/primary/FASE7_RESUMEN.md", 
         "Resumen Fase 7"),
        (base_path / "PROYECTO_RESUMEN_COMPLETO.md", 
         "Resumen Completo del Proyecto"),
        (base_path / "tests/test_fase7_dashboards.py", 
         "Tests Fase 7"),
    ]
    
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_ok = False
    
    print()
    
    # Verificar directorios
    print("📂 DIRECTORIOS:")
    print("-"*70)
    
    dirs_to_check = [
        (base_path / "src/adapters/primary/rest_api/views", 
         "Views directory"),
        (base_path / "src/adapters/primary/rest_api", 
         "REST API directory"),
        (base_path / "tests", 
         "Tests directory"),
    ]
    
    for dirpath, description in dirs_to_check:
        if not check_directory_exists(dirpath, description):
            all_ok = False
    
    print()
    
    # Verificar contenido de archivos clave
    print("🔍 VERIFICACIÓN DE CONTENIDO:")
    print("-"*70)
    
    # Verificar que urls_api_v2.py incluye DashboardViewSet y ReportsViewSet
    urls_file = base_path / "src/adapters/primary/rest_api/urls_api_v2.py"
    if urls_file.exists():
        with open(urls_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'DashboardViewSet' in content:
            print("✅ urls_api_v2.py incluye DashboardViewSet")
        else:
            print("❌ urls_api_v2.py NO incluye DashboardViewSet")
            all_ok = False
        
        if 'ReportsViewSet' in content:
            print("✅ urls_api_v2.py incluye ReportsViewSet")
        else:
            print("❌ urls_api_v2.py NO incluye ReportsViewSet")
            all_ok = False
        
        if "router.register(r'dashboards'" in content:
            print("✅ Router registra 'dashboards'")
        else:
            print("❌ Router NO registra 'dashboards'")
            all_ok = False
        
        if "router.register(r'reports'" in content:
            print("✅ Router registra 'reports'")
        else:
            print("❌ Router NO registra 'reports'")
            all_ok = False
    
    print()
    
    # Contar endpoints implementados
    print("📊 ESTADÍSTICAS:")
    print("-"*70)
    
    dashboards_file = base_path / "src/adapters/primary/rest_api/views/dashboards.py"
    if dashboards_file.exists():
        with open(dashboards_file, 'r', encoding='utf-8') as f:
            content = f.read()
        dashboard_endpoints = content.count("@action")
        print(f"✅ Dashboard endpoints: {dashboard_endpoints}")
    
    reports_file = base_path / "src/adapters/primary/rest_api/views/reports.py"
    if reports_file.exists():
        with open(reports_file, 'r', encoding='utf-8') as f:
            content = f.read()
        report_endpoints = content.count("@action")
        print(f"✅ Report endpoints: {report_endpoints}")
    
    print()
    
    # Resultado final
    print("="*70)
    if all_ok:
        print("✅ ¡VERIFICACIÓN COMPLETADA EXITOSAMENTE!")
        print("   Todos los archivos de Fase 7 están en su lugar.")
        print()
        print("🚀 PRÓXIMOS PASOS:")
        print("   1. Habilitar REST API v2 en config/urls.py")
        print("   2. Ejecutar migraciones si es necesario")
        print("   3. Iniciar servidor: python manage.py runserver")
        print("   4. Probar endpoints:")
        print("      - GET /api/v2/dashboards/general/")
        print("      - GET /api/v2/reports/practices/")
        print("      - GET /api/v2/dashboards/charts/?type=practices_status")
        print()
        print("📚 DOCUMENTACIÓN:")
        print("   - Fase 7: src/adapters/primary/FASE7_RESUMEN.md")
        print("   - Dashboards: src/adapters/primary/rest_api/views/README_DASHBOARDS.md")
        print("   - Completo: PROYECTO_RESUMEN_COMPLETO.md")
        return 0
    else:
        print("❌ VERIFICACIÓN FALLÓ")
        print("   Algunos archivos están faltando o mal configurados.")
        print("   Revisa los errores anteriores.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
