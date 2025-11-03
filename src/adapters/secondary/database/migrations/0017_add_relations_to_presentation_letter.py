# Generated manually on 2025-11-02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0016_add_presentation_letter_request'),
    ]

    operations = [
        # Agregar campo ForeignKey a School (Escuela)
        migrations.AddField(
            model_name='presentationletterrequest',
            name='escuela',
            field=models.ForeignKey(
                blank=True,
                help_text='Escuela profesional del estudiante',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='presentation_letters',
                to='database.school',
                verbose_name='Escuela Profesional'
            ),
        ),
        
        # Agregar campo ForeignKey a Company (Empresa)
        migrations.AddField(
            model_name='presentationletterrequest',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                help_text='Empresa donde realizará la práctica (opcional)',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='presentation_letters',
                to='database.company',
                verbose_name='Empresa'
            ),
        ),
        
        # Modificar campo ep para hacerlo opcional (auto-rellenado)
        migrations.AlterField(
            model_name='presentationletterrequest',
            name='ep',
            field=models.CharField(
                blank=True,
                help_text='Auto-rellenado desde escuela.nombre',
                max_length=200,
                verbose_name='E.P. (Escuela Profesional)'
            ),
        ),
        
        # Modificar campo company_name para hacerlo opcional
        migrations.AlterField(
            model_name='presentationletterrequest',
            name='company_name',
            field=models.CharField(
                blank=True,
                help_text='Auto-rellenado desde empresa.nombre si se selecciona empresa',
                max_length=255,
                verbose_name='Nombre de la Empresa'
            ),
        ),
        
        # Modificar campo company_address para hacerlo opcional
        migrations.AlterField(
            model_name='presentationletterrequest',
            name='company_address',
            field=models.TextField(
                blank=True,
                help_text='Auto-rellenado desde empresa.direccion si se selecciona empresa',
                verbose_name='Dirección de la Empresa'
            ),
        ),
        
        # Modificar help_text de company_representative
        migrations.AlterField(
            model_name='presentationletterrequest',
            name='company_representative',
            field=models.CharField(
                help_text='Persona de contacto específica para esta solicitud',
                max_length=200,
                verbose_name='Nombre del Representante'
            ),
        ),
        
        # Modificar help_text de company_phone
        migrations.AlterField(
            model_name='presentationletterrequest',
            name='company_phone',
            field=models.CharField(
                help_text='Teléfono de contacto (puede ser diferente al de la empresa)',
                max_length=50,
                verbose_name='Teléfono - Fax'
            ),
        ),
        
        # Agregar índices para mejorar performance
        migrations.AddIndex(
            model_name='presentationletterrequest',
            index=models.Index(fields=['escuela', 'status'], name='pres_lett_escuela_status_idx'),
        ),
        migrations.AddIndex(
            model_name='presentationletterrequest',
            index=models.Index(fields=['empresa', 'status'], name='pres_lett_empresa_status_idx'),
        ),
    ]
