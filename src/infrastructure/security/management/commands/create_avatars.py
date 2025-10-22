"""
Comando de gestión para crear avatares en la base de datos.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from src.adapters.secondary.database.models import Avatar


class Command(BaseCommand):
    help = 'Crea avatares por rol en la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Elimina todos los avatares existentes antes de crear nuevos',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Eliminando avatares existentes...'))
            Avatar.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Avatares eliminados.'))

        # Avatares por rol con URLs simples
        avatares_data = {
            'PRACTICANTE': [
                # 48 avatares para practicantes (estudiantes)
                'https://img.freepik.com/free-vector/businessman-character-avatar-isolated_24877-60111.jpg',
                'https://img.freepik.com/free-vector/young-prince-vector-illustration_1308-174367.jpg',
                'https://img.freepik.com/free-vector/smiling-young-man-illustration_1308-174669.jpg',
                'https://img.freepik.com/free-vector/hand-drawn-side-profile-cartoon-illustration_23-2150503804.jpg',
                'https://img.freepik.com/free-vector/mysterious-mafia-man-smoking-cigarette_52683-34828.jpg',
                'https://img.freepik.com/free-vector/young-man-with-glasses-avatar_1308-175763.jpg',
                'https://img.freepik.com/free-vector/portrait-white-man-isolated_23-2148834708.jpg',
                'https://img.freepik.com/free-vector/boy-avatar-cartoon-character-portrait_18591-50445.jpg',
                'https://img.freepik.com/free-vector/young-man-head-with-different-facial-expressions_52683-32635.jpg',
                'https://img.freepik.com/free-vector/portrait-man-cartoon-style_52683-15016.jpg',
                'https://img.freepik.com/free-vector/woman-avatar-portrait-young-female-character_24877-60110.jpg',
                'https://img.freepik.com/free-vector/young-woman-with-long-hair-avatar_1308-175764.jpg',
                'https://img.freepik.com/free-vector/girl-avatar-cartoon-character-portrait_18591-50446.jpg',
                'https://img.freepik.com/free-vector/portrait-beautiful-young-woman-with-bob-haircut_1308-174670.jpg',
                'https://img.freepik.com/free-vector/smiling-woman-portrait_1308-174671.jpg',
                'https://img.freepik.com/free-vector/young-woman-head-with-different-facial-expressions_52683-32636.jpg',
                'https://img.freepik.com/free-vector/portrait-woman-cartoon-style_52683-15017.jpg',
                'https://img.freepik.com/free-vector/woman-with-glasses-avatar_1308-175765.jpg',
                'https://img.freepik.com/free-vector/portrait-white-woman-isolated_23-2148834709.jpg',
                'https://img.freepik.com/free-vector/young-beautiful-woman-looking-surprised_1308-174672.jpg',
                'https://img.freepik.com/free-vector/man-with-beard-avatar_1308-175766.jpg',
                'https://img.freepik.com/free-vector/cool-man-with-sunglasses-avatar_1308-175767.jpg',
                'https://img.freepik.com/free-vector/student-avatar-illustration_24877-60112.jpg',
                'https://img.freepik.com/free-vector/young-student-character-avatar_24877-60113.jpg',
                'https://img.freepik.com/free-vector/graduate-student-avatar_1308-175768.jpg',
                'https://img.freepik.com/free-vector/smart-student-with-books-avatar_1308-175769.jpg',
                'https://img.freepik.com/free-vector/casual-student-avatar_1308-175770.jpg',
                'https://img.freepik.com/free-vector/tech-student-avatar_1308-175771.jpg',
                'https://img.freepik.com/free-vector/creative-student-avatar_1308-175772.jpg',
                'https://img.freepik.com/free-vector/art-student-avatar_1308-175773.jpg',
                'https://img.freepik.com/free-vector/science-student-avatar_1308-175774.jpg',
                'https://img.freepik.com/free-vector/engineering-student-avatar_1308-175775.jpg',
                'https://img.freepik.com/free-vector/business-student-avatar_1308-175776.jpg',
                'https://img.freepik.com/free-vector/medical-student-avatar_1308-175777.jpg',
                'https://img.freepik.com/free-vector/law-student-avatar_1308-175778.jpg',
                'https://img.freepik.com/free-vector/music-student-avatar_1308-175779.jpg',
                'https://img.freepik.com/free-vector/sports-student-avatar_1308-175780.jpg',
                'https://img.freepik.com/free-vector/language-student-avatar_1308-175781.jpg',
                'https://img.freepik.com/free-vector/psychology-student-avatar_1308-175782.jpg',
                'https://img.freepik.com/free-vector/communication-student-avatar_1308-175783.jpg',
                'https://img.freepik.com/free-vector/design-student-avatar_1308-175784.jpg',
                'https://img.freepik.com/free-vector/architecture-student-avatar_1308-175785.jpg',
                'https://img.freepik.com/free-vector/economics-student-avatar_1308-175786.jpg',
                'https://img.freepik.com/free-vector/marketing-student-avatar_1308-175787.jpg',
                'https://img.freepik.com/free-vector/finance-student-avatar_1308-175788.jpg',
                'https://img.freepik.com/free-vector/tourism-student-avatar_1308-175789.jpg',
                'https://img.freepik.com/free-vector/education-student-avatar_1308-175790.jpg',
                'https://img.freepik.com/free-vector/social-student-avatar_1308-175791.jpg',
                'https://img.freepik.com/free-vector/environmental-student-avatar_1308-175792.jpg',
            ],
            'SECRETARIA': [
                'https://img.freepik.com/free-vector/secretary-avatar-illustration_24877-60114.jpg',
                'https://img.freepik.com/free-vector/office-woman-avatar_1308-175793.jpg',
            ],
            'SUPERVISOR': [
                'https://img.freepik.com/free-vector/supervisor-avatar-illustration_24877-60115.jpg',
                'https://img.freepik.com/free-vector/manager-avatar_1308-175794.jpg',
            ],
            'COORDINADOR': [
                'https://img.freepik.com/free-vector/coordinator-avatar-illustration_24877-60116.jpg',
                'https://img.freepik.com/free-vector/team-leader-avatar_1308-175795.jpg',
            ],
            'ADMINISTRADOR': [
                'https://img.freepik.com/free-vector/administrator-avatar-illustration_24877-60117.jpg',
            ],
        }

        total_created = 0
        
        with transaction.atomic():
            for role, avatares in avatares_data.items():
                self.stdout.write(f'Creando avatares para rol: {role}')
                
                for avatar_url in avatares:
                    avatar, created = Avatar.objects.get_or_create(
                        url=avatar_url,
                        role=role,
                        defaults={
                            'is_active': True
                        }
                    )
                    
                    if created:
                        total_created += 1
                        self.stdout.write(f'  ✓ Creado: {avatar.id}')
                    else:
                        self.stdout.write(f'  - Ya existe: {avatar.id}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\n¡Comando completado! Se crearon {total_created} avatares nuevos.\n'
                f'Total de avatares en la base de datos: {Avatar.objects.count()}'
            )
        )
        
        # Mostrar resumen por rol
        self.stdout.write('\n📊 Resumen por rol:')
        for role, _ in Avatar.ROLE_CHOICES:
            count = Avatar.objects.filter(role=role, is_active=True).count()
            self.stdout.write(f'  {role}: {count} avatares')
