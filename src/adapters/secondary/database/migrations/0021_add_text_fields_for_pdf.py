# Generated manually on 2024-11-02
"""
Migración para agregar campos de texto (ep, company_name, company_address)
que se auto-llenan desde las relaciones para generación de PDF.

Estos campos se mantienen separados de las ForeignKeys para permitir:
1. Generación de PDF sin depender de las relaciones
2. Conservar datos históricos si se elimina/modifica la empresa o escuela
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0020_fix_assigned_secretary_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='presentationletterrequest',
            name='ep',
            field=models.CharField(
                verbose_name='E.P. (Escuela Profesional)',
                max_length=200,
                help_text='Auto-rellenado desde escuela.nombre',
                blank=True,
                default=''
            ),
        ),
        migrations.AddField(
            model_name='presentationletterrequest',
            name='company_name',
            field=models.CharField(
                verbose_name='Nombre de la Empresa',
                max_length=255,
                help_text='Auto-rellenado desde empresa.nombre si se selecciona empresa',
                blank=True,
                default=''
            ),
        ),
        migrations.AddField(
            model_name='presentationletterrequest',
            name='company_address',
            field=models.TextField(
                verbose_name='Dirección de la Empresa',
                help_text='Auto-rellenado desde empresa.direccion si se selecciona empresa',
                blank=True,
                default=''
            ),
        ),
    ]
