"""
Script para arreglar el tipo de dato de django_admin_log.user_id
"""
import sys
import os
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def fix_admin_log_table():
    """Arregla el tipo de dato de user_id en django_admin_log."""
    with connection.cursor() as cursor:
        # Primero verificar la estructura actual
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'django_admin_log' 
            AND column_name = 'user_id';
        """)
        result = cursor.fetchone()
        
        if result:
            column_name, data_type = result
            print(f"Tipo actual de {column_name}: {data_type}")
            
            if data_type == 'uuid':
                print("🔧 Arreglando tipo de dato...")
                
                # Eliminar la constraint FK si existe
                cursor.execute("""
                    SELECT constraint_name 
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'django_admin_log' 
                    AND constraint_type = 'FOREIGN KEY';
                """)
                constraints = cursor.fetchall()
                
                for (constraint,) in constraints:
                    print(f"   Eliminando constraint: {constraint}")
                    cursor.execute(f"ALTER TABLE django_admin_log DROP CONSTRAINT {constraint};")
                
                # Cambiar el tipo de dato
                print("   Cambiando tipo de dato de UUID a INTEGER...")
                cursor.execute("""
                    ALTER TABLE django_admin_log 
                    ALTER COLUMN user_id TYPE INTEGER USING user_id::text::integer;
                """)
                
                # Recrear la FK
                print("   Recreando foreign key...")
                cursor.execute("""
                    ALTER TABLE django_admin_log 
                    ADD CONSTRAINT django_admin_log_user_id_fkey 
                    FOREIGN KEY (user_id) 
                    REFERENCES upeu_usuario(id) 
                    ON DELETE CASCADE;
                """)
                
                print("✅ Tabla django_admin_log arreglada correctamente")
            else:
                print("✅ El tipo de dato ya es correcto (INTEGER)")
        else:
            print("❌ No se encontró la columna user_id en django_admin_log")

if __name__ == '__main__':
    try:
        fix_admin_log_table()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
