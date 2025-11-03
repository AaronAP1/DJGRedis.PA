#!/usr/bin/env python
"""
Script para migrar datos existentes de PresentationLetterRequest.

Migra:
1. Escuela desde el perfil del estudiante
2. Empresa buscando por nombre (si existe)

Uso:
    python manage.py shell < scripts/migrate_presentation_letter_data.py
    O ejecutar dentro de Django shell
"""

# Este script debe ejecutarse dentro del contexto de Django
# Importar modelos directamente
try:
    from src.adapters.secondary.database.models import (
        PresentationLetterRequest,
        School,
        Company
    )
    from django.db import models as django_models
    from django.db.models import Count
except ImportError:
    print("❌ Error: Este script debe ejecutarse dentro del contexto de Django")
    print("   Usa: python manage.py shell")
    print("   Luego: exec(open('scripts/migrate_presentation_letter_data.py').read())")
    import sys
    sys.exit(1)


def migrate_escuela_relations():
    """Migrar relaciones de escuela desde el perfil del estudiante."""
    print("=" * 80)
    print("MIGRANDO RELACIONES DE ESCUELA")
    print("=" * 80)
    
    letters_without_escuela = PresentationLetterRequest.objects.filter(escuela__isnull=True)
    total = letters_without_escuela.count()
    migrated = 0
    
    print(f"\n📊 Total de cartas sin escuela asignada: {total}")
    
    for letter in letters_without_escuela:
        if letter.student and letter.student.escuela:
            letter.escuela = letter.student.escuela
            letter.ep = letter.student.escuela.nombre
            letter.save(update_fields=['escuela', 'ep'])
            migrated += 1
            print(f"✅ Carta #{letter.id}: Asignada escuela '{letter.escuela.nombre}'")
        else:
            print(f"⚠️  Carta #{letter.id}: Estudiante sin escuela asignada")
    
    print(f"\n✅ Migradas {migrated}/{total} cartas con escuela")
    print("=" * 80)


def migrate_empresa_relations():
    """Migrar relaciones de empresa buscando por nombre."""
    print("\n" + "=" * 80)
    print("MIGRANDO RELACIONES DE EMPRESA")
    print("=" * 80)
    
    letters_without_empresa = PresentationLetterRequest.objects.filter(empresa__isnull=True)
    total = letters_without_empresa.count()
    found = 0
    not_found = 0
    
    print(f"\n📊 Total de cartas sin empresa asignada: {total}")
    
    for letter in letters_without_empresa:
        if not letter.company_name:
            print(f"⚠️  Carta #{letter.id}: Sin nombre de empresa")
            not_found += 1
            continue
        
        # Buscar empresa por nombre (case-insensitive)
        empresa = Company.objects.filter(
            nombre__iexact=letter.company_name.strip()
        ).first()
        
        if empresa:
            letter.empresa = empresa
            # Auto-rellenar datos desde la empresa
            if not letter.company_address:
                letter.company_address = empresa.direccion or ''
            letter.save(update_fields=['empresa', 'company_address'])
            found += 1
            print(f"✅ Carta #{letter.id}: Empresa encontrada '{empresa.nombre}' (RUC: {empresa.ruc})")
        else:
            print(f"ℹ️  Carta #{letter.id}: Empresa '{letter.company_name}' NO encontrada en BD")
            not_found += 1
    
    print(f"\n✅ Encontradas {found}/{total} empresas existentes")
    print(f"ℹ️  {not_found} empresas no encontradas (quedarán como texto)")
    print("=" * 80)


def create_missing_empresas():
    """
    Crear empresas faltantes para cartas sin empresa asignada.
    
    NOTA: Este proceso es OPCIONAL y debe revisarse manualmente.
    """
    print("\n" + "=" * 80)
    print("CREAR EMPRESAS FALTANTES (OPCIONAL)")
    print("=" * 80)
    
    letters_without_empresa = PresentationLetterRequest.objects.filter(empresa__isnull=True)
    
    if not letters_without_empresa.exists():
        print("\n✅ No hay cartas sin empresa asignada")
        return
    
    print(f"\n📊 Cartas sin empresa: {letters_without_empresa.count()}")
    print("\n⚠️  ADVERTENCIA: Este proceso creará empresas en estado PENDIENTE")
    print("    Las empresas deben ser validadas manualmente después.")
    
    response = input("\n¿Desea crear las empresas faltantes? (s/N): ")
    
    if response.lower() != 's':
        print("❌ Creación de empresas cancelada")
        return
    
    created = 0
    
    for letter in letters_without_empresa:
        if not letter.company_name:
            continue
        
        # Verificar que no exista
        if Company.objects.filter(nombre__iexact=letter.company_name.strip()).exists():
            continue
        
        # Crear empresa en estado PENDIENTE
        empresa = Company.objects.create(
            nombre=letter.company_name.strip(),
            ruc='00000000000',  # RUC temporal - debe actualizarse
            direccion=letter.company_address or '',
            telefono=letter.company_phone or '',
            estado='PENDIENTE'
        )
        
        # Asignar a la carta
        letter.empresa = empresa
        letter.save(update_fields=['empresa'])
        
        created += 1
        print(f"✅ Empresa creada: '{empresa.nombre}' (ID: {empresa.id}) - Estado: PENDIENTE")
    
    print(f"\n✅ Creadas {created} empresas nuevas")
    print("⚠️  IMPORTANTE: Actualizar los RUCs y validar las empresas creadas")
    print("=" * 80)


def generate_report():
    """Generar reporte de migración."""
    print("\n" + "=" * 80)
    print("REPORTE DE MIGRACIÓN")
    print("=" * 80)
    
    total_letters = PresentationLetterRequest.objects.count()
    with_escuela = PresentationLetterRequest.objects.filter(escuela__isnull=False).count()
    with_empresa = PresentationLetterRequest.objects.filter(empresa__isnull=False).count()
    
    print(f"\n📊 Estadísticas:")
    print(f"   Total de cartas: {total_letters}")
    print(f"   Con escuela asignada: {with_escuela} ({with_escuela/total_letters*100:.1f}%)" if total_letters > 0 else "   Con escuela asignada: 0")
    print(f"   Con empresa asignada: {with_empresa} ({with_empresa/total_letters*100:.1f}%)" if total_letters > 0 else "   Con empresa asignada: 0")
    
    # Empresas más solicitadas
    print("\n📈 Top 5 Empresas más solicitadas:")
    top_empresas = (
        PresentationLetterRequest.objects
        .filter(empresa__isnull=False)
        .values('empresa__nombre', 'empresa__ruc')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )
    
    for i, emp in enumerate(top_empresas, 1):
        print(f"   {i}. {emp['empresa__nombre']} (RUC: {emp['empresa__ruc']}) - {emp['total']} cartas")
    
    # Escuelas más activas
    print("\n📈 Top 5 Escuelas más activas:")
    top_escuelas = (
        PresentationLetterRequest.objects
        .filter(escuela__isnull=False)
        .values('escuela__nombre', 'escuela__codigo')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )
    
    for i, esc in enumerate(top_escuelas, 1):
        print(f"   {i}. {esc['escuela__nombre']} ({esc['escuela__codigo']}) - {esc['total']} cartas")
    
    print("=" * 80)


def main():
    """Ejecutar migración completa."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "MIGRACIÓN DE DATOS - CARTAS DE PRESENTACIÓN" + " " * 20 + "║")
    print("╚" + "=" * 78 + "╝")
    
    try:
        # Paso 1: Migrar escuelas
        migrate_escuela_relations()
        
        # Paso 2: Migrar empresas
        migrate_empresa_relations()
        
        # Paso 3: Crear empresas faltantes (opcional)
        create_missing_empresas()
        
        # Paso 4: Generar reporte
        generate_report()
        
        print("\n✅ Migración completada exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error durante la migración: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
