# Generated manually on 2024-11-02
"""
Migración para eliminar campos de texto que ya no se necesitan.
Se ejecuta con IF EXISTS para evitar errores en producción.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0020_fix_assigned_secretary_type'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Eliminar campos de texto si existen
                ALTER TABLE presentation_letter_requests 
                DROP COLUMN IF EXISTS ep CASCADE;
                
                ALTER TABLE presentation_letter_requests 
                DROP COLUMN IF EXISTS company_name CASCADE;
                
                ALTER TABLE presentation_letter_requests 
                DROP COLUMN IF EXISTS company_address CASCADE;
            """,
            reverse_sql="""
                -- No hay reverse porque estos campos ya no se usan
            """
        ),
    ]
