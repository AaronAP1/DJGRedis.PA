"""
Comando para crear usuarios de prueba con cada rol del sistema.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from src.adapters.secondary.database.models import Role, Permission, RolePermission, Student, Company, Supervisor

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

    def create_roles_with_permissions(self):
        """Crea roles con permisos por defecto si no existen."""
        self.stdout.write('🔧 Verificando roles y permisos por defecto...\n')
        
        # Definir roles con sus permisos por defecto
        roles_data = {
            'ADMINISTRADOR': {
                'name': 'Administrador',
                'description': 'Acceso completo al sistema',
                'permissions': [
                    'users.view', 'users.add', 'users.change', 'users.delete',
                    'roles.view', 'roles.add', 'roles.change', 'roles.delete',
                    'permissions.view', 'permissions.add', 'permissions.change', 'permissions.delete',
                    'students.view', 'students.add', 'students.change', 'students.delete',
                    'companies.view', 'companies.add', 'companies.change', 'companies.delete',
                    'practices.view', 'practices.add', 'practices.change', 'practices.delete',
                    'reports.view', 'reports.generate', 'system.configure'
                ]
            },
            'COORDINADOR': {
                'name': 'Coordinador',
                'description': 'Gestión de prácticas y supervisión',
                'permissions': [
                    'practices.view', 'practices.add', 'practices.change',
                    'students.view', 'students.change',
                    'companies.view', 'companies.add', 'companies.change',
                    'supervisors.view', 'supervisors.add', 'supervisors.change',
                    'reports.view', 'reports.generate'
                ]
            },
            'SECRETARIA': {
                'name': 'Secretaria',
                'description': 'Gestión administrativa y documentos',
                'permissions': [
                    'students.view', 'students.add', 'students.change',
                    'documents.view', 'documents.add', 'documents.change',
                    'reports.view', 'communications.send'
                ]
            },
            'SUPERVISOR': {
                'name': 'Supervisor',
                'description': 'Supervisión de prácticas asignadas',
                'permissions': [
                    'practices.view', 'practices.change',
                    'students.view', 'evaluations.add', 'evaluations.change',
                    'reports.view'
                ]
            },
            'PRACTICANTE': {
                'name': 'Practicante',
                'description': 'Acceso básico para estudiantes',
                'permissions': [
                    'profile.view', 'profile.change',
                    'documents.view', 'documents.add',
                    'practices.view'
                ]
            }
        }
        
        created_roles = 0
        created_permissions = 0
        
        with transaction.atomic():
            # Crear permisos únicos
            all_permissions = set()
            for role_data in roles_data.values():
                all_permissions.update(role_data['permissions'])
            
            for perm_code in all_permissions:
                perm, created = Permission.objects.get_or_create(
                    code=perm_code,
                    defaults={
                        'name': perm_code.replace('.', ' ').replace('_', ' ').title(),
                        'description': f'Permiso para {perm_code}',
                        'module': perm_code.split('.')[0] if '.' in perm_code else 'general',
                        'is_active': True
                    }
                )
                if created:
                    created_permissions += 1
                    self.stdout.write(f'  ✅ Permiso creado: {perm_code}')
            
            # Crear roles con permisos
            for role_code, role_data in roles_data.items():
                role, created = Role.objects.get_or_create(
                    code=role_code,
                    defaults={
                        'name': role_data['name'],
                        'description': role_data['description'],
                        'is_active': True,
                        'is_system': True
                    }
                )
                
                if created:
                    created_roles += 1
                    self.stdout.write(f'  ✅ Rol creado: {role_code}')
                
                # Asignar permisos al rol
                current_perms = set(role.permissions.values_list('code', flat=True))
                expected_perms = set(role_data['permissions'])
                
                # Agregar permisos faltantes
                for perm_code in expected_perms - current_perms:
                    try:
                        permission = Permission.objects.get(code=perm_code)
                        role.permissions.add(permission)
                        self.stdout.write(f'    ➕ Permiso agregado a {role_code}: {perm_code}')
                    except Permission.DoesNotExist:
                        self.stdout.write(f'    ⚠️  Permiso no encontrado: {perm_code}')
        
        self.stdout.write(f'📊 Resumen: {created_roles} roles creados, {created_permissions} permisos creados\n')

    def handle(self, *args, **options):
        password = options.get('password', 'Test1234')
        force = options.get('force', False)
        
        self.stdout.write('👥 Creando usuarios de prueba con roles...\n')

        # Crear roles y permisos por defecto
        self.create_roles_with_permissions()

        # Verificar que existan roles
        roles = Role.objects.filter(is_active=True)
        if not roles.exists():
            self.stdout.write(self.style.ERROR(
                '❌ No hay roles en el sistema después de la creación'
            ))
            return

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
                student, created = Student.objects.get_or_create(
                    user=user,
                    defaults={
                        'codigo_estudiante': f'2024{user.id.int % 100000:06d}',  # Formato: 2024001234
                        'documento_tipo': 'DNI',
                        'documento_numero': f'{user.id.int % 100000000:08d}',
                        'telefono': '999888777',
                        'direccion': 'Av. Universitaria 123, Lima',
                        'carrera': 'Ingeniería de Sistemas',
                        'semestre_actual': 8,  # Campo correcto
                        'promedio_ponderado': 15.50,
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
