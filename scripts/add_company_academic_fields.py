"""
Script para agregar campos grado_academico y cargo_academico a la tabla upeu_empresa.
"""
import os
import django
import sys

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def add_company_academic_fields():
    """Agrega los campos grado_academico y cargo_academico a upeu_empresa."""
    
    sql_statements = [
        """
        ALTER TABLE upeu_empresa 
        ADD COLUMN IF NOT EXISTS grado_academico VARCHAR(100);
        """,
        """
        ALTER TABLE upeu_empresa 
        ADD COLUMN IF NOT EXISTS cargo_academico VARCHAR(100);
        """,
        """
        COMMENT ON COLUMN upeu_empresa.grado_academico 
        IS 'Grado académico del representante (Ej: Ingeniero, Licenciado, Magister, Doctor)';
        """,
        """
        COMMENT ON COLUMN upeu_empresa.cargo_academico 
        IS 'Cargo académico del representante (Ej: Gerente General, Director, Jefe de RRHH)';
        """
    ]
    
    print("=" * 80)
    print("AGREGANDO CAMPOS A upeu_empresa")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        for i, sql in enumerate(sql_statements, 1):
            print(f"\n[{i}/{len(sql_statements)}] Ejecutando SQL...")
            print(sql.strip())
            cursor.execute(sql)
            print("✅ OK")
    
    # Verificar que se agregaron
    print("\n" + "=" * 80)
    print("VERIFICANDO COLUMNAS AGREGADAS")
    print("=" * 80)
    
    verify_sql = """
    SELECT column_name, data_type, character_maximum_length, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'upeu_empresa'
    AND column_name IN ('grado_academico', 'cargo_academico')
    ORDER BY column_name;
    """
    
    with connection.cursor() as cursor:
        cursor.execute(verify_sql)
        results = cursor.fetchall()
        
        if results:
            print("\n✅ Campos agregados exitosamente:\n")
            print(f"{'Campo':<20} {'Tipo':<15} {'Longitud':<10} {'Nullable'}")
            print("-" * 60)
            for row in results:
                column_name, data_type, max_length, is_nullable = row
                print(f"{column_name:<20} {data_type:<15} {max_length or 'N/A':<10} {is_nullable}")
        else:
            print("❌ No se encontraron las columnas")
    
    print("\n" + "=" * 80)
    print("✅ PROCESO COMPLETADO")
    print("=" * 80)

if __name__ == '__main__':
    try:
        add_company_academic_fields()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
