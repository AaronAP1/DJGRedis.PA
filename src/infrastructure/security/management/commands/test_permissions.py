"""
Comando para probar el sistema de permisos personalizados.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from src.adapters.secondary.database.models import Permission, UserPermission
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Prueba el sistema de permisos personalizados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list-users',
            action='store_true',
            help='Lista todos los usuarios con sus permisos'
        )
        parser.add_argument(
            '--list-permissions',
            action='store_true',
            help='Lista todos los permisos disponibles'
        )
        parser.add_argument(
            '--grant',
            nargs=3,
            metavar=('USER_UUID', 'PERMISSION_ID', 'REASON'),
            help='Otorga un permiso a un usuario'
        )
        parser.add_argument(
            '--revoke',
            nargs=3,
            metavar=('USER_UUID', 'PERMISSION_ID', 'REASON'),
            help='Revoca un permiso de un usuario'
        )

    def handle(self, *args, **options):
        if options['list_users']:
            self.list_users_with_permissions()
        elif options['list_permissions']:
            self.list_permissions()
        elif options['grant']:
            user_uuid, perm_id, reason = options['grant']
            self.grant_permission(user_uuid, perm_id, reason)
        elif options['revoke']:
            user_uuid, perm_id, reason = options['revoke']
            self.revoke_permission(user_uuid, perm_id, reason)
        else:
            self.stdout.write(self.style.WARNING('Usa --help para ver las opciones disponibles'))

    def list_users_with_permissions(self):
        """Lista todos los usuarios con sus permisos detallados."""
        self.stdout.write(self.style.SUCCESS('\n=== USUARIOS Y SUS PERMISOS ===\n'))
        
        users = User.objects.filter(is_active=True).exclude(role='PRACTICANTE')
        
        for user in users:
            self.stdout.write(f"\n👤 {user.get_full_name()} ({user.email})")
            self.stdout.write(f"   UUID: {user.pk}")
            self.stdout.write(f"   Rol: {user.role}")
            
            # Permisos del rol
            if user.role_obj:
                role_perms = user.role_obj.permissions.filter(is_active=True)
                self.stdout.write(f"\n   📋 Permisos del rol ({role_perms.count()}):")
                for perm in role_perms:
                    self.stdout.write(f"      ✅ {perm.code} - {perm.name} (ID: {perm.pk})")
            
            # Permisos personalizados
            custom_perms = user.custom_permissions.filter(permission__is_active=True)
            if custom_perms.exists():
                self.stdout.write(f"\n   🎯 Permisos personalizados ({custom_perms.count()}):")
                for custom in custom_perms:
                    icon = "🟢" if custom.permission_type == 'GRANT' else "🔴"
                    status = "OTORGADO" if custom.permission_type == 'GRANT' else "REVOCADO"
                    self.stdout.write(f"      {icon} {custom.permission.code} - {status}")
                    self.stdout.write(f"         Razón: {custom.reason}")
                    self.stdout.write(f"         Fecha: {custom.granted_at}")
                    if custom.expires_at:
                        self.stdout.write(f"         Expira: {custom.expires_at}")
            
            # Permisos finales efectivos
            all_perms = user.get_all_permissions()
            self.stdout.write(f"\n   ⚡ Permisos efectivos finales ({len(all_perms)}):")
            for perm_code in sorted(all_perms):
                self.stdout.write(f"      • {perm_code}")
            
            self.stdout.write("-" * 80)

    def list_permissions(self):
        """Lista todos los permisos disponibles."""
        self.stdout.write(self.style.SUCCESS('\n=== PERMISOS DISPONIBLES ===\n'))
        
        permissions = Permission.objects.filter(is_active=True).order_by('module', 'code')
        current_module = None
        
        for perm in permissions:
            if perm.module != current_module:
                current_module = perm.module
                self.stdout.write(f"\n📁 Módulo: {current_module}")
                self.stdout.write("-" * 50)
            
            self.stdout.write(f"   ID: {perm.pk}")
            self.stdout.write(f"   Código: {perm.code}")
            self.stdout.write(f"   Nombre: {perm.name}")
            self.stdout.write(f"   Descripción: {perm.description or 'Sin descripción'}")
            self.stdout.write("")

    def grant_permission(self, user_uuid, perm_id, reason):
        """Otorga un permiso a un usuario."""
        try:
            user = User.objects.get(pk=user_uuid)
            permission = Permission.objects.get(pk=perm_id)
            
            # Crear o actualizar permiso personalizado
            user_perm, created = UserPermission.objects.update_or_create(
                user=user,
                permission=permission,
                defaults={
                    'permission_type': 'GRANT',
                    'reason': reason,
                    'expires_at': timezone.now() + timedelta(days=365)
                }
            )
            
            action = "creado" if created else "actualizado"
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Permiso {permission.code} {action} para {user.get_full_name()}'
                )
            )
            
            # Mostrar permisos actuales del usuario
            all_perms = user.get_all_permissions()
            self.stdout.write(f"\n🔍 Permisos actuales del usuario ({len(all_perms)}):")
            for perm_code in sorted(all_perms):
                self.stdout.write(f"   • {perm_code}")
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Usuario con UUID {user_uuid} no encontrado'))
        except Permission.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Permiso con ID {perm_id} no encontrado'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))

    def revoke_permission(self, user_uuid, perm_id, reason):
        """Revoca un permiso de un usuario."""
        try:
            user = User.objects.get(pk=user_uuid)
            permission = Permission.objects.get(pk=perm_id)
            
            # Crear o actualizar para revocar
            user_perm, created = UserPermission.objects.update_or_create(
                user=user,
                permission=permission,
                defaults={
                    'permission_type': 'REVOKE',
                    'reason': reason
                }
            )
            
            action = "creado" if created else "actualizado"
            self.stdout.write(
                self.style.SUCCESS(
                    f'🔴 Permiso {permission.code} revocado para {user.get_full_name()}'
                )
            )
            
            # Mostrar permisos actuales del usuario
            all_perms = user.get_all_permissions()
            self.stdout.write(f"\n🔍 Permisos actuales del usuario ({len(all_perms)}):")
            for perm_code in sorted(all_perms):
                self.stdout.write(f"   • {perm_code}")
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Usuario con UUID {user_uuid} no encontrado'))
        except Permission.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Permiso con ID {perm_id} no encontrado'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
