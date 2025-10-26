"""
Comando para crear usuarios de prueba con cada rol del sistema.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from src.adapters.secondary.database.models import Role, StudentProfile, Company, SupervisorProfile

User = get_user_model()


class Command(BaseCommand):
    help = "Crea usuarios de prueba con cada rol del sistema"

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            default='Test1234',
            help='Contraseña para todos los usuarios de prueba (default: Test1234)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Elimina usuarios existentes antes de crear',
        )

    # NOTA: Función deshabilitada - Permission ya no existe en BD real
    # Los permisos ahora están en Role.permisos como JSONB
    def create_roles_with_permissions(self):
        """DESHABILITADO - Los permisos ahora están en JSONB en upeu_rol."""
        self.stdout.write('⚠️  Función create_roles_with_permissions DESHABILITADA')
        self.stdout.write('   Los permisos ahora están en Role.permisos como JSONB\n')
        return
        
    # def create_roles_with_permissions(self):
    #     """Crea roles con permisos por defecto si no existen."""
    #     # CÓDIGO COMENTADO - usar JSONB en su lugar
    #     pass

    def handle(self, *args, **options):
        password = options.get('password', 'Test1234')
        force = options.get('force', False)
        
        self.stdout.write('👥 Creando usuarios de prueba con roles...\n')

        # Crear roles y permisos por defecto
        # DESHABILITADO - Permission no existe más
        # self.create_roles_with_permissions()

        # Verificar que existan roles
        roles = Role.objects.filter(nombre__isnull=False)  # Cambio: usar nombre en vez de is_active
        if not roles.exists():
            self.stdout.write(self.style.WARNING(
                '⚠️  No hay roles en el sistema. Crear roles manualmente o usando insert_test_data_real.sql'
            ))
            # No salir, continuar con usuarios sin roles
        
        # Usuarios de prueba por rol (cada uno con su contraseña específica)
        test_users = [
            {
                'role_code': 'ADMINISTRADOR',
                'email': 'admin@upeu.edu.pe',
                'username': 'admin.test',
                'first_name': 'Administrador',
                'last_name': 'Test',
                'password': 'Admin123',
            },
            {
                'role_code': 'COORDINADOR',
                'email': 'coordinador@upeu.edu.pe',
                'username': 'coordinador.test',
                'first_name': 'Coordinador',
                'last_name': 'Test',
                'password': 'Coord123',
            },
            {
                'role_code': 'SECRETARIA',
                'email': 'secretaria@upeu.edu.pe',
                'username': 'secretaria.test',
                'first_name': 'Secretaria',
                'last_name': 'Test',
                'password': 'Secre123',
            },
            {
                'role_code': 'SUPERVISOR',
                'email': 'supervisor@upeu.edu.pe',
                'username': 'supervisor.test',
                'first_name': 'Supervisor',
                'last_name': 'Test',
                'password': 'Super123',
            },
            {
                'role_code': 'PRACTICANTE',
                'email': 'practicante@upeu.edu.pe',
                'username': 'practicante.test',
                'first_name': 'Practicante',
                'last_name': 'Test',
                'password': 'Pract123',
            },
        ]

        created = 0
        skipped = 0
        deleted = 0

        for user_data in test_users:
            email = user_data['email']
            role_code = user_data['role_code']
            
            # Buscar el rol
            try:
                role = Role.objects.get(code=role_code, is_active=True)
            except Role.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'  ❌ Rol "{role_code}" no encontrado - OMITIDO'
                ))
                skipped += 1
                continue

            # Verificar si existe el usuario
            existing = User.objects.filter(email=email).first()
            
            if existing:
                if force:
                    existing.delete()
                    deleted += 1
                    self.stdout.write(self.style.WARNING(
                        f'  🗑️  Usuario {email} eliminado'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'  ⚠️  Usuario {email} ya existe - OMITIDO (usa --force para reemplazar)'
                    ))
                    skipped += 1
                    continue

            # Usar contraseña específica del usuario o la del parámetro --password
            user_password = user_data.get('password', password)
            
            # Crear usuario
            try:
                if role_code == 'ADMINISTRADOR':
                    # Crear superusuario para administrador
                    user = User.objects.create_superuser(
                        email=email,
                        password=user_password,
                        username=user_data['username'],
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],
                        role=role_code,  # Legacy field
                        role_obj=role,    # Nuevo sistema
                    )
                else:
                    # Crear usuario normal para otros roles
                    user = User.objects.create_user(
                        email=email,
                        password=user_password,
                        username=user_data['username'],
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],
                        role=role_code,  # Legacy field
                        role_obj=role,    # Nuevo sistema
                        is_active=True,
                    )
                
                self.stdout.write(self.style.SUCCESS(
                    f'  ✅ {email} → {role.name}'
                ))
                self.stdout.write(
                    f'     Usuario: {user.username} | Contraseña: {user_password}'
                )
                
                # Crear perfiles adicionales según el rol
                self._create_additional_profiles(user, role_code)
                
                created += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'  ❌ Error creando {email}: {str(e)}'
                ))
                skipped += 1

        # Resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write('📊 RESUMEN:')
        self.stdout.write(self.style.SUCCESS(f'  • Usuarios creados: {created}'))
        if deleted > 0:
            self.stdout.write(self.style.WARNING(f'  • Usuarios eliminados: {deleted}'))
        if skipped > 0:
            self.stdout.write(self.style.WARNING(f'  • Omitidos: {skipped}'))
        self.stdout.write('='*60 + '\n')

        if created > 0:
            self.stdout.write(self.style.SUCCESS('✨ Usuarios de prueba creados exitosamente!\n'))
            self.stdout.write('🔑 Credenciales de acceso:')
            for user_data in test_users:
                if not User.objects.filter(email=user_data['email']).exists():
                    continue
                user_password = user_data.get('password', password)
                role_name = Role.objects.get(code=user_data['role_code']).name
                self.stdout.write(f'  • {user_data["email"]} / {user_password} ({role_name})')
            self.stdout.write('')
    
    def _create_additional_profiles(self, user, role_code):
        """Crea perfiles adicionales según el rol del usuario."""
        try:
            if role_code == 'PRACTICANTE':
                # Crear perfil de estudiante
                student, created = StudentProfile.objects.get_or_create(
                    usuario=user,
                    defaults={
                        'codigo': f'2024{user.id % 100000:06d}',  # Formato: 2024001234
                        'semestre': 8,
                        'promedio': 15.50,
                        'fecha_nacimiento': '2000-01-01',  # Requerido
                        'estado_academico': 'REGULAR',
                    }
                )
                if created:
                    self.stdout.write(f'     → Perfil de estudiante creado: {student.codigo_estudiante}')
            
            # Solo PRACTICANTE necesita perfil adicional
            # SUPERVISOR, COORDINADOR, SECRETARIA, ADMINISTRADOR = solo usuario base
        
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f'     ⚠️  Error creando perfil adicional: {str(e)}'
            ))
