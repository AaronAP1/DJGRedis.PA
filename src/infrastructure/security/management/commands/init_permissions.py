"""
Comando para inicializar permisos y roles del sistema.
"""

from django.core.management.base import BaseCommand
from src.adapters.secondary.database.models import Permission, Role, RolePermission


class Command(BaseCommand):
    help = "Inicializa permisos y roles del sistema de gestión de prácticas"

    def handle(self, *args, **options):
        self.stdout.write('🔧 Inicializando permisos y roles...\n')

        # ===== CREAR PERMISOS =====
        permissions_data = [
            # Usuarios
            {'code': 'users.view', 'name': 'Ver usuarios', 'module': 'users'},
            {'code': 'users.create', 'name': 'Crear usuarios', 'module': 'users'},
            {'code': 'users.edit', 'name': 'Editar usuarios', 'module': 'users'},
            {'code': 'users.delete', 'name': 'Eliminar usuarios', 'module': 'users'},
            {'code': 'users.import', 'name': 'Importar usuarios', 'module': 'users'},
            {'code': 'users.export', 'name': 'Exportar usuarios', 'module': 'users'},
            
            # Estudiantes
            {'code': 'students.view', 'name': 'Ver estudiantes', 'module': 'students'},
            {'code': 'students.create', 'name': 'Crear estudiantes', 'module': 'students'},
            {'code': 'students.edit', 'name': 'Editar estudiantes', 'module': 'students'},
            {'code': 'students.delete', 'name': 'Eliminar estudiantes', 'module': 'students'},
            
            # Empresas
            {'code': 'companies.view', 'name': 'Ver empresas', 'module': 'companies'},
            {'code': 'companies.create', 'name': 'Crear empresas', 'module': 'companies'},
            {'code': 'companies.edit', 'name': 'Editar empresas', 'module': 'companies'},
            {'code': 'companies.delete', 'name': 'Eliminar empresas', 'module': 'companies'},
            {'code': 'companies.validate', 'name': 'Validar empresas', 'module': 'companies'},
            
            # Supervisores
            {'code': 'supervisors.view', 'name': 'Ver supervisores', 'module': 'supervisors'},
            {'code': 'supervisors.create', 'name': 'Crear supervisores', 'module': 'supervisors'},
            {'code': 'supervisors.edit', 'name': 'Editar supervisores', 'module': 'supervisors'},
            {'code': 'supervisors.delete', 'name': 'Eliminar supervisores', 'module': 'supervisors'},
            
            # Prácticas
            {'code': 'practices.view', 'name': 'Ver prácticas', 'module': 'practices'},
            {'code': 'practices.view_all', 'name': 'Ver todas las prácticas', 'module': 'practices'},
            {'code': 'practices.create', 'name': 'Crear prácticas', 'module': 'practices'},
            {'code': 'practices.edit', 'name': 'Editar prácticas', 'module': 'practices'},
            {'code': 'practices.delete', 'name': 'Eliminar prácticas', 'module': 'practices'},
            {'code': 'practices.approve', 'name': 'Aprobar prácticas', 'module': 'practices'},
            {'code': 'practices.cancel', 'name': 'Cancelar prácticas', 'module': 'practices'},
            
            # Documentos
            {'code': 'documents.view', 'name': 'Ver documentos', 'module': 'documents'},
            {'code': 'documents.upload', 'name': 'Subir documentos', 'module': 'documents'},
            {'code': 'documents.download', 'name': 'Descargar documentos', 'module': 'documents'},
            {'code': 'documents.delete', 'name': 'Eliminar documentos', 'module': 'documents'},
            {'code': 'documents.approve', 'name': 'Aprobar documentos', 'module': 'documents'},
            
            # Notificaciones
            {'code': 'notifications.view', 'name': 'Ver notificaciones', 'module': 'notifications'},
            {'code': 'notifications.create', 'name': 'Crear notificaciones', 'module': 'notifications'},
            {'code': 'notifications.send', 'name': 'Enviar notificaciones', 'module': 'notifications'},
            
            # Reportes y estadísticas
            {'code': 'reports.view', 'name': 'Ver reportes', 'module': 'reports'},
            {'code': 'reports.export', 'name': 'Exportar reportes', 'module': 'reports'},
            {'code': 'statistics.view', 'name': 'Ver estadísticas', 'module': 'statistics'},
            
            # Administración
            {'code': 'admin.roles', 'name': 'Gestionar roles', 'module': 'admin'},
            {'code': 'admin.permissions', 'name': 'Gestionar permisos', 'module': 'admin'},
            {'code': 'admin.settings', 'name': 'Configuración del sistema', 'module': 'admin'},
        ]

        created_perms = 0
        for perm_data in permissions_data:
            perm, created = Permission.objects.get_or_create(
                code=perm_data['code'],
                defaults={
                    'name': perm_data['name'],
                    'module': perm_data.get('module', 'general')
                }
            )
            if created:
                created_perms += 1
                self.stdout.write(f"  ✅ Permiso creado: {perm.code}")

        self.stdout.write(self.style.SUCCESS(f"\n📋 {created_perms} permisos nuevos creados\n"))

        # ===== CREAR ROLES =====
        roles_config = {
            'ADMINISTRADOR': {
                'name': 'Administrador',
                'description': 'Acceso completo al sistema',
                'permissions': '*'  # Todos los permisos
            },
            'COORDINADOR': {
                'name': 'Coordinador de Prácticas',
                'description': 'Gestiona prácticas, estudiantes y empresas',
                'permissions': [
                    'users.view', 'students.*', 'companies.*', 'supervisors.*',
                    'practices.*', 'documents.*', 'notifications.*',
                    'reports.*', 'statistics.view'
                ]
            },
            'SECRETARIA': {
                'name': 'Secretaria',
                'description': 'Gestión administrativa y documentación',
                'permissions': [
                    'users.view', 'students.view', 'students.edit',
                    'companies.view', 'companies.edit',
                    'practices.view', 'practices.view_all', 'practices.edit',
                    'documents.*', 'notifications.view', 'notifications.create'
                ]
            },
            'SUPERVISOR': {
                'name': 'Supervisor de Empresa',
                'description': 'Supervisa prácticas de su empresa',
                'permissions': [
                    'practices.view', 'practices.edit',
                    'documents.view', 'documents.upload', 'documents.download',
                    'notifications.view'
                ]
            },
            'PRACTICANTE': {
                'name': 'Practicante',
                'description': 'Usuario estudiante en prácticas',
                'permissions': [
                    'practices.view', 'documents.view', 'documents.upload',
                    'documents.download', 'notifications.view'
                ]
            }
        }

        all_perms = list(Permission.objects.filter(is_active=True))
        created_roles = 0

        for code, config in roles_config.items():
            role, created = Role.objects.get_or_create(
                code=code,
                defaults={
                    'name': config['name'],
                    'description': config['description'],
                    'is_system': True
                }
            )

            if created:
                created_roles += 1
                self.stdout.write(f"\n  ✅ Rol creado: {role.name}")

            # Asignar permisos
            if config['permissions'] == '*':
                # Todos los permisos
                perms_to_assign = all_perms
            else:
                # Filtrar permisos específicos
                perms_to_assign = []
                for perm_pattern in config['permissions']:
                    if perm_pattern.endswith('.*'):
                        # Patrón de módulo completo
                        module = perm_pattern[:-2]
                        perms_to_assign.extend([p for p in all_perms if p.code.startswith(module + '.')])
                    else:
                        # Permiso específico
                        perm = next((p for p in all_perms if p.code == perm_pattern), None)
                        if perm:
                            perms_to_assign.append(perm)

            # Asignar permisos al rol
            for perm in perms_to_assign:
                RolePermission.objects.get_or_create(
                    role=role,
                    permission=perm
                )

            self.stdout.write(f"     → {len(perms_to_assign)} permisos asignados")

        self.stdout.write(self.style.SUCCESS(f"\n👥 {created_roles} roles nuevos creados"))
        self.stdout.write(self.style.SUCCESS(f"\n✨ Inicialización completada exitosamente!\n"))
