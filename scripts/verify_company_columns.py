"""
Verificar si los campos grado_academico y cargo_academico existen en upeu_empresa
"""
import os
import django
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def verify_columns():
    """Verificar columnas en upeu_empresa."""
    
    print("=" * 80)
    print("VERIFICANDO COLUMNAS EN upeu_empresa")
    print("=" * 80)
    
    sql = """
    SELECT column_name, data_type, character_maximum_length, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'upeu_empresa'
    ORDER BY ordinal_position;
    """
    
    with connection.cursor() as cursor:
        cursor.execute(sql)
        columns = cursor.fetchall()
        
        print(f"\n📊 Total de columnas: {len(columns)}\n")
        print(f"{'Columna':<25} {'Tipo':<20} {'Longitud':<10} {'Nullable'}")
        print("-" * 80)
        
        found_grado = False
        found_cargo = False
        
        for col in columns:
            column_name, data_type, max_length, is_nullable = col
            print(f"{column_name:<25} {data_type:<20} {max_length or 'N/A':<10} {is_nullable}")
            
            if column_name == 'grado_academico':
                found_grado = True
            if column_name == 'cargo_academico':
                found_cargo = True
        
        print("\n" + "=" * 80)
        print("RESULTADO:")
        print("=" * 80)
        print(f"✅ grado_academico encontrado: {found_grado}")
        print(f"✅ cargo_academico encontrado: {found_cargo}")
        
        if not found_grado or not found_cargo:
            print("\n⚠️  LOS CAMPOS NO EXISTEN EN LA BASE DE DATOS")
            print("Ejecutando ALTER TABLE ahora...")
            
            add_columns_sql = [
                "ALTER TABLE upeu_empresa ADD COLUMN IF NOT EXISTS grado_academico VARCHAR(100);",
                "ALTER TABLE upeu_empresa ADD COLUMN IF NOT EXISTS cargo_academico VARCHAR(100);"
            ]
            
            for sql_cmd in add_columns_sql:
                print(f"\n▶️  {sql_cmd}")
                cursor.execute(sql_cmd)
            
            print("\n✅ Columnas agregadas. Verificando nuevamente...")
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns
                WHERE table_name = 'upeu_empresa'
                AND column_name IN ('grado_academico', 'cargo_academico')
                ORDER BY column_name;
            """)
            
            new_cols = cursor.fetchall()
            for col in new_cols:
                print(f"  ✓ {col[0]}")

if __name__ == '__main__':
    verify_columns()
