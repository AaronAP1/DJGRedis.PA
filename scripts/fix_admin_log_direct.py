"""
Script para arreglar django_admin_log sin necesidad de django_filters
Ejecuta SQL directo con psycopg2
"""
import psycopg2

# Configuración de conexión
DB_CONFIG = {
    'dbname': 'upeu_ppp_system',
    'user': 'upeu_admin',
    'password': 'upeu_contra_2024',
    'host': 'localhost',
    'port': '5432'
}

SQL_SCRIPT = """
-- ============================================
-- Arreglar django_admin_log
-- ============================================

-- Paso 1: Eliminar FK constraint de django_admin_log
DO $$
DECLARE
    constraint_name text;
BEGIN
    SELECT tc.constraint_name INTO constraint_name
    FROM information_schema.table_constraints tc
    WHERE tc.table_name = 'django_admin_log' 
    AND tc.constraint_type = 'FOREIGN KEY'
    AND tc.constraint_name LIKE '%user_id%';
    
    IF constraint_name IS NOT NULL THEN
        EXECUTE 'ALTER TABLE django_admin_log DROP CONSTRAINT ' || constraint_name;
        RAISE NOTICE 'Constraint % eliminada', constraint_name;
    END IF;
END $$;

-- Paso 2: Limpiar datos existentes de django_admin_log
TRUNCATE TABLE django_admin_log;

-- Paso 3: Cambiar tipo de dato user_id en django_admin_log
ALTER TABLE django_admin_log 
ALTER COLUMN user_id TYPE INTEGER USING NULL;

-- Paso 4: Recrear FK en django_admin_log
ALTER TABLE django_admin_log 
ADD CONSTRAINT django_admin_log_user_id_fkey 
FOREIGN KEY (user_id) 
REFERENCES upeu_usuario(id) 
ON DELETE CASCADE;

-- ============================================
-- Arreglar token_blacklist_outstandingtoken
-- ============================================

-- Paso 5: Verificar si existe la tabla token_blacklist_outstandingtoken
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'token_blacklist_outstandingtoken') THEN
        -- Eliminar FK constraint de token_blacklist_outstandingtoken
        DECLARE
            constraint_name text;
        BEGIN
            SELECT tc.constraint_name INTO constraint_name
            FROM information_schema.table_constraints tc
            WHERE tc.table_name = 'token_blacklist_outstandingtoken' 
            AND tc.constraint_type = 'FOREIGN KEY'
            AND tc.constraint_name LIKE '%user_id%';
            
            IF constraint_name IS NOT NULL THEN
                EXECUTE 'ALTER TABLE token_blacklist_outstandingtoken DROP CONSTRAINT ' || constraint_name;
                RAISE NOTICE 'Constraint % eliminada', constraint_name;
            END IF;
        END;

        -- Limpiar datos existentes
        TRUNCATE TABLE token_blacklist_outstandingtoken CASCADE;

        -- Cambiar tipo de dato user_id
        ALTER TABLE token_blacklist_outstandingtoken 
        ALTER COLUMN user_id TYPE INTEGER USING NULL;

        -- Recrear FK
        ALTER TABLE token_blacklist_outstandingtoken 
        ADD CONSTRAINT token_blacklist_outstandingtoken_user_id_fkey 
        FOREIGN KEY (user_id) 
        REFERENCES upeu_usuario(id) 
        ON DELETE CASCADE;
        
        RAISE NOTICE 'Tabla token_blacklist_outstandingtoken arreglada';
    END IF;
END $$;

-- ============================================
-- Arreglar axes_accesslog y axes_accessattempt si existen
-- ============================================

DO $$
BEGIN
    -- Arreglar axes_accesslog
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'axes_accesslog') THEN
        IF EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'axes_accesslog' 
            AND column_name = 'user_id'
        ) THEN
            -- Eliminar FK constraint
            DECLARE
                constraint_name text;
            BEGIN
                SELECT tc.constraint_name INTO constraint_name
                FROM information_schema.table_constraints tc
                WHERE tc.table_name = 'axes_accesslog' 
                AND tc.constraint_type = 'FOREIGN KEY'
                AND tc.constraint_name LIKE '%user_id%';
                
                IF constraint_name IS NOT NULL THEN
                    EXECUTE 'ALTER TABLE axes_accesslog DROP CONSTRAINT ' || constraint_name;
                END IF;
            END;

            -- Cambiar tipo de dato
            ALTER TABLE axes_accesslog 
            ALTER COLUMN user_id TYPE INTEGER USING user_id::text::integer;

            -- Recrear FK
            ALTER TABLE axes_accesslog 
            ADD CONSTRAINT axes_accesslog_user_id_fkey 
            FOREIGN KEY (user_id) 
            REFERENCES upeu_usuario(id) 
            ON DELETE CASCADE;
            
            RAISE NOTICE 'Tabla axes_accesslog arreglada';
        END IF;
    END IF;

    -- Arreglar axes_accessattempt
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'axes_accessattempt') THEN
        IF EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'axes_accessattempt' 
            AND column_name = 'user_id'
        ) THEN
            -- Eliminar FK constraint
            DECLARE
                constraint_name text;
            BEGIN
                SELECT tc.constraint_name INTO constraint_name
                FROM information_schema.table_constraints tc
                WHERE tc.table_name = 'axes_accessattempt' 
                AND tc.constraint_type = 'FOREIGN KEY'
                AND tc.constraint_name LIKE '%user_id%';
                
                IF constraint_name IS NOT NULL THEN
                    EXECUTE 'ALTER TABLE axes_accessattempt DROP CONSTRAINT ' || constraint_name;
                END IF;
            END;

            -- Cambiar tipo de dato
            ALTER TABLE axes_accessattempt 
            ALTER COLUMN user_id TYPE INTEGER USING user_id::text::integer;

            -- Recrear FK
            ALTER TABLE axes_accessattempt 
            ADD CONSTRAINT axes_accessattempt_user_id_fkey 
            FOREIGN KEY (user_id) 
            REFERENCES upeu_usuario(id) 
            ON DELETE CASCADE;
            
            RAISE NOTICE 'Tabla axes_accessattempt arreglada';
        END IF;
    END IF;
END $$;
"""

def fix_admin_log():
    """Arregla el tipo de dato de user_id en todas las tablas que lo requieren."""
    try:
        # Conectar a PostgreSQL
        print("Conectando a PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Lista de tablas a verificar
        tables_to_check = [
            'django_admin_log',
            'token_blacklist_outstandingtoken',
            'axes_accesslog',
            'axes_accessattempt'
        ]
        
        print("\n🔍 Verificando tablas con user_id...\n")
        
        for table_name in tables_to_check:
            # Verificar si la tabla existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (table_name,))
            
            if not cursor.fetchone()[0]:
                print(f"⏭️  {table_name}: No existe (omitiendo)")
                continue
            
            # Verificar tipo actual de user_id
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = %s 
                AND column_name = 'user_id';
            """, (table_name,))
            
            result = cursor.fetchone()
            
            if result:
                column_name, data_type = result
                print(f"📋 {table_name}.{column_name}: {data_type}", end="")
                
                if data_type == 'uuid':
                    print(" ❌ (necesita corrección)")
                else:
                    print(" ✅")
            else:
                print(f"⏭️  {table_name}: No tiene columna user_id")
        
        print("\n🔧 Ejecutando correcciones...\n")
        
        # Ejecutar el script SQL completo
        cursor.execute(SQL_SCRIPT)
        
        print("\n✅ Verificando resultados finales...\n")
        
        # Verificar el cambio en todas las tablas
        for table_name in tables_to_check:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (table_name,))
            
            if not cursor.fetchone()[0]:
                continue
                
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = %s 
                AND column_name = 'user_id';
            """, (table_name,))
            
            result = cursor.fetchone()
            if result:
                column_name, data_type = result
                print(f"✅ {table_name}.{column_name}: {data_type}")
        
        print("\n🎉 Todas las tablas corregidas correctamente")
        print("🚀 Django admin debería funcionar completamente ahora")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Error de PostgreSQL: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_admin_log()
