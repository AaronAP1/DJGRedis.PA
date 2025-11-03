# Generated manually on 2025-11-02 - Fix column types

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0018_remove_presentationletterrequest_pres_lett_escuela_status_idx_and_more'),
    ]

    operations = [
        # Primero eliminar las columnas mal creadas usando SQL directo
        migrations.RunSQL(
            sql="ALTER TABLE presentation_letter_requests DROP COLUMN IF EXISTS escuela_id CASCADE;",
            reverse_sql="-- No reverse"
        ),
        migrations.RunSQL(
            sql="ALTER TABLE presentation_letter_requests DROP COLUMN IF EXISTS empresa_id CASCADE;",
            reverse_sql="-- No reverse"
        ),
        
        # Crear las columnas con el tipo correcto (INTEGER para ForeignKey a AutoField)
        migrations.RunSQL(
            sql="""
                ALTER TABLE presentation_letter_requests 
                ADD COLUMN escuela_id INTEGER NULL 
                REFERENCES upeu_escuela(id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
            """,
            reverse_sql="ALTER TABLE presentation_letter_requests DROP COLUMN escuela_id;"
        ),
        migrations.RunSQL(
            sql="""
                ALTER TABLE presentation_letter_requests 
                ADD COLUMN empresa_id INTEGER NULL 
                REFERENCES upeu_empresa(id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
            """,
            reverse_sql="ALTER TABLE presentation_letter_requests DROP COLUMN empresa_id;"
        ),
        
        # Crear índices para performance
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS pres_lett_escuela_idx ON presentation_letter_requests(escuela_id);",
            reverse_sql="DROP INDEX IF EXISTS pres_lett_escuela_idx;"
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS pres_lett_empresa_idx ON presentation_letter_requests(empresa_id);",
            reverse_sql="DROP INDEX IF EXISTS pres_lett_empresa_idx;"
        ),
    ]
