# Generated manually for JWT PURO cleanup

from django.db import migrations


def cleanup_opaque_tables(apps, schema_editor):
    """Limpia tablas opacas si existen - para JWT PURO"""
    db_alias = schema_editor.connection.alias
    
    with schema_editor.connection.cursor() as cursor:
        # Verificar y eliminar session_activities si existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'session_activities'
            );
        """)
        if cursor.fetchone()[0]:
            cursor.execute("DROP TABLE session_activities CASCADE;")
            print("✅ Tabla session_activities eliminada")
        else:
            print("ℹ️  Tabla session_activities no existe")
        
        # Verificar y eliminar opaque_sessions si existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'opaque_sessions'
            );
        """)
        if cursor.fetchone()[0]:
            cursor.execute("DROP TABLE opaque_sessions CASCADE;")
            print("✅ Tabla opaque_sessions eliminada")
        else:
            print("ℹ️  Tabla opaque_sessions no existe")


def reverse_cleanup(apps, schema_editor):
    """No hay reversa - JWT PURO es permanente"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0008_add_roles_permissions_system'),
    ]

    operations = [
        migrations.RunPython(
            cleanup_opaque_tables,
            reverse_cleanup,
            hints={'target_db': 'default'}
        ),
    ]
