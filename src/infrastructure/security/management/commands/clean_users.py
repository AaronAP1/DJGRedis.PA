"""
Comando para limpiar TODOS los usuarios de la BD con sus relaciones.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from src.adapters.secondary.database.models import StudentProfile, SupervisorProfile, Company

User = get_user_model()


class Command(BaseCommand):
    help = "Elimina TODOS los usuarios de la BD con todas sus relaciones"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra lo que se eliminaría sin aplicar cambios',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirma que quieres eliminar TODOS los usuarios',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        confirm = options.get('confirm', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODO DRY-RUN: No se aplicarán cambios\n'))
        elif not confirm:
            self.stdout.write(self.style.ERROR(
                '⚠️  ATENCIÓN: Este comando eliminará TODOS los usuarios y sus datos relacionados.\n'
                'Usa --confirm para proceder o --dry-run para ver qué se eliminaría.\n'
            ))
            return

        self.stdout.write('🧹 Limpiando TODOS los usuarios de la BD...\n')

        # Buscar TODOS los usuarios (incluyendo superusuarios)
        all_users = User.objects.all()
        self.stdout.write(self.style.WARNING('⚠️  ELIMINANDO TODOS LOS USUARIOS (incluyendo superusuarios)'))

        if not all_users.exists():
            self.stdout.write(self.style.SUCCESS('✅ No hay usuarios para limpiar.\n'))
            return

        total_users = all_users.count()
        self.stdout.write(f'📊 Usuarios a procesar: {total_users}\n')

        deleted_students = 0
        deleted_supervisors = 0
        deleted_users = 0

        with transaction.atomic():
            for user in all_users:
                self.stdout.write(f'🔍 Procesando: {user.email} (role: {user.role})')

                # 1. Eliminar perfil de estudiante si existe
                try:
                    student = StudentProfile.objects.get(usuario=user)
                    if dry_run:
                        self.stdout.write(f'  📚 Eliminaría perfil de estudiante: {student.codigo}')
                    else:
                        student.delete()
                        self.stdout.write(f'  ✅ Perfil de estudiante eliminado: {student.codigo}')
                    deleted_students += 1
                except StudentProfile.DoesNotExist:
                    pass

                # 2. Eliminar perfil de supervisor si existe
                try:
                    supervisor = SupervisorProfile.objects.get(usuario=user)
                    if dry_run:
                        self.stdout.write(f'  👔 Eliminaría perfil de supervisor: {user.get_full_name()}')
                    else:
                        supervisor.delete()
                        self.stdout.write(f'  ✅ Perfil de supervisor eliminado: {user.get_full_name()}')
                    deleted_supervisors += 1
                except SupervisorProfile.DoesNotExist:
                    pass

                # 3. Eliminar usuario (sin verificar relaciones - forzar eliminación)
                if dry_run:
                    self.stdout.write(f'  👤 Eliminaría usuario: {user.email}')
                else:
                    user.delete()
                    self.stdout.write(self.style.SUCCESS(f'  ✅ Usuario eliminado: {user.email}'))
                deleted_users += 1

        # Resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write('📊 RESUMEN:')
        if dry_run:
            self.stdout.write(f'  • Estudiantes a eliminar: {deleted_students}')
            self.stdout.write(f'  • Supervisores a eliminar: {deleted_supervisors}')
            self.stdout.write(f'  • Usuarios a eliminar: {deleted_users}')
        else:
            self.stdout.write(self.style.SUCCESS(f'  • Estudiantes eliminados: {deleted_students}'))
            self.stdout.write(self.style.SUCCESS(f'  • Supervisores eliminados: {deleted_supervisors}'))
            self.stdout.write(self.style.SUCCESS(f'  • Usuarios eliminados: {deleted_users}'))
        self.stdout.write('='*60 + '\n')

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '💡 Ejecuta con --confirm para aplicar los cambios'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('✨ Limpieza completada!\n'))
            self.stdout.write('🔄 Ahora puedes crear usuarios nuevos con:')
            self.stdout.write('   python manage.py create_users')
