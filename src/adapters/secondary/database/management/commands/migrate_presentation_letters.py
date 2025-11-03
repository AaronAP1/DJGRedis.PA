"""
Django management command para migrar datos de PresentationLetterRequest.
"""

from django.core.management.base import BaseCommand
from django.db.models import Count
from src.adapters.secondary.database.models import (
    PresentationLetterRequest,
    School,
    Company
)


class Command(BaseCommand):
    help = 'Migra datos existentes de PresentationLetterRequest a las nuevas relaciones'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("MIGRACIÓN DE DATOS - CARTAS DE PRESENTACIÓN"))
        self.stdout.write("=" * 80)
        
        # Migrar escuelas
        self.migrate_escuela_relations()
        
        # Migrar empresas
        self.migrate_empresa_relations()
        
        # Generar reporte
        self.generate_report()
        
        self.stdout.write(self.style.SUCCESS("\n✅ Migración completada exitosamente"))

    def migrate_escuela_relations(self):
        """Migrar relaciones de escuela desde el perfil del estudiante."""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("MIGRANDO RELACIONES DE ESCUELA")
        self.stdout.write("=" * 80)
        
        letters_without_escuela = PresentationLetterRequest.objects.filter(escuela__isnull=True)
        total = letters_without_escuela.count()
        migrated = 0
        
        self.stdout.write(f"\n📊 Total de cartas sin escuela asignada: {total}")
        
        for letter in letters_without_escuela:
            try:
                # Verificar si tiene student_id antes de acceder a student
                if hasattr(letter, 'student_id') and letter.student_id:
                    if letter.student.escuela:
                        letter.escuela = letter.student.escuela
                        letter.ep = letter.student.escuela.nombre
                        letter.save(update_fields=['escuela', 'ep'])
                        migrated += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"✅ Carta #{letter.id}: Asignada escuela '{letter.escuela.nombre}'"
                        ))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"⚠️  Carta #{letter.id}: Estudiante sin escuela asignada en su perfil"
                        ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️  Carta #{letter.id}: Sin estudiante asignado (carta de prueba)"
                    ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"❌ Carta #{letter.id}: Error - {str(e)}"
                ))
        
        self.stdout.write(f"\n✅ Migradas {migrated}/{total} cartas con escuela")
        self.stdout.write("=" * 80)

    def migrate_empresa_relations(self):
        """Migrar relaciones de empresa buscando por nombre."""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("MIGRANDO RELACIONES DE EMPRESA")
        self.stdout.write("=" * 80)
        
        letters_without_empresa = PresentationLetterRequest.objects.filter(empresa__isnull=True)
        total = letters_without_empresa.count()
        found = 0
        not_found = 0
        
        self.stdout.write(f"\n📊 Total de cartas sin empresa asignada: {total}")
        
        for letter in letters_without_empresa:
            if not letter.company_name:
                self.stdout.write(self.style.WARNING(
                    f"⚠️  Carta #{letter.id}: Sin nombre de empresa"
                ))
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
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Carta #{letter.id}: Empresa encontrada '{empresa.nombre}' (RUC: {empresa.ruc})"
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"ℹ️  Carta #{letter.id}: Empresa '{letter.company_name}' NO encontrada en BD"
                ))
                not_found += 1
        
        self.stdout.write(f"\n✅ Encontradas {found}/{total} empresas existentes")
        self.stdout.write(f"ℹ️  {not_found} empresas no encontradas (quedarán como texto)")
        self.stdout.write("=" * 80)

    def generate_report(self):
        """Generar reporte de migración."""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("REPORTE DE MIGRACIÓN")
        self.stdout.write("=" * 80)
        
        total_letters = PresentationLetterRequest.objects.count()
        with_escuela = PresentationLetterRequest.objects.filter(escuela__isnull=False).count()
        with_empresa = PresentationLetterRequest.objects.filter(empresa__isnull=False).count()
        
        self.stdout.write(f"\n📊 Estadísticas:")
        self.stdout.write(f"   Total de cartas: {total_letters}")
        
        if total_letters > 0:
            self.stdout.write(
                f"   Con escuela asignada: {with_escuela} ({with_escuela/total_letters*100:.1f}%)"
            )
            self.stdout.write(
                f"   Con empresa asignada: {with_empresa} ({with_empresa/total_letters*100:.1f}%)"
            )
        else:
            self.stdout.write("   No hay cartas de presentación registradas")
            return
        
        # Empresas más solicitadas
        self.stdout.write("\n📈 Top 5 Empresas más solicitadas:")
        top_empresas = (
            PresentationLetterRequest.objects
            .filter(empresa__isnull=False)
            .values('empresa__nombre', 'empresa__ruc')
            .annotate(total=Count('id'))
            .order_by('-total')[:5]
        )
        
        if top_empresas:
            for i, emp in enumerate(top_empresas, 1):
                self.stdout.write(
                    f"   {i}. {emp['empresa__nombre']} (RUC: {emp['empresa__ruc']}) - {emp['total']} cartas"
                )
        else:
            self.stdout.write("   No hay empresas asignadas aún")
        
        # Escuelas más activas
        self.stdout.write("\n📈 Top 5 Escuelas más activas:")
        top_escuelas = (
            PresentationLetterRequest.objects
            .filter(escuela__isnull=False)
            .values('escuela__nombre', 'escuela__codigo')
            .annotate(total=Count('id'))
            .order_by('-total')[:5]
        )
        
        if top_escuelas:
            for i, esc in enumerate(top_escuelas, 1):
                self.stdout.write(
                    f"   {i}. {esc['escuela__nombre']} ({esc['escuela__codigo']}) - {esc['total']} cartas"
                )
        else:
            self.stdout.write("   No hay escuelas asignadas aún")
        
        self.stdout.write("=" * 80)
