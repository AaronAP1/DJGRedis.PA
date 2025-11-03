# Generated manually on 2024-11-02
"""
Migración para corregir el tipo de assigned_secretary_id en presentation_letter_requests.

PROBLEMA: El campo assigned_secretary_id se creó como UUID pero debe ser INTEGER
porque upeu_usuario.id es INTEGER (AutoField).

SOLUCIÓN: Usar RunSQL para recrear la columna con el tipo correcto.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0019_fix_foreign_key_types'),
    ]

    operations = [
        migrations.RunSQL(
            # Forward: Cambiar assigned_secretary_id de UUID a INTEGER
            sql="""
                -- 1. Eliminar columna UUID actual
                ALTER TABLE presentation_letter_requests 
                DROP COLUMN IF EXISTS assigned_secretary_id CASCADE;
                
                -- 2. Crear columna INTEGER con ForeignKey a upeu_usuario
                ALTER TABLE presentation_letter_requests 
                ADD COLUMN assigned_secretary_id INTEGER;
                
                -- 3. Crear ForeignKey constraint
                ALTER TABLE presentation_letter_requests
                ADD CONSTRAINT pres_lett_assigned_secretary_fk
                FOREIGN KEY (assigned_secretary_id)
                REFERENCES upeu_usuario(id)
                ON DELETE SET NULL;
                
                -- 4. Crear índice para optimización
                CREATE INDEX pres_lett_assigned_secretary_idx
                ON presentation_letter_requests(assigned_secretary_id);
            """,
            # Reverse: Volver a UUID (solo para rollback)
            reverse_sql="""
                ALTER TABLE presentation_letter_requests 
                DROP COLUMN IF EXISTS assigned_secretary_id CASCADE;
                
                ALTER TABLE presentation_letter_requests 
                ADD COLUMN assigned_secretary_id UUID;
            """
        ),
    ]
