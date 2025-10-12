"""
Mutations GraphQL para gestión de Roles y Permisos.
"""

import graphene
from graphql_jwt.decorators import login_required
from django.contrib.auth import get_user_model
from graphene import relay
from src.adapters.primary.graphql_api.types import (
    PermissionType, RoleType, UserPermissionType, PermissionInput, RoleInput,
    UserType
)
from src.adapters.secondary.database.models import (
    Permission, Role, RolePermission, UserPermission
)
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


# ===== MUTATIONS DE PERMISOS DE USUARIO =====

class GrantUserPermission(graphene.Mutation):
    """Otorga un permiso adicional a un usuario (override)."""
    
    class Arguments:
        user_id = graphene.ID(required=True)
        permission_id = graphene.ID(required=True)
        reason = graphene.String()
    
    success = graphene.Boolean()
    message = graphene.String()
    user_permission = graphene.Field(UserPermissionType)
    
    @staticmethod
    @login_required
    def mutate(root, info, user_id, permission_id, reason=None):
        user = info.context.user
        
        # Solo administradores pueden otorgar permisos
        if user.role != 'ADMINISTRADOR':
            return GrantUserPermission(
                success=False,
                message="No tienes permisos para otorgar permisos a usuarios",
                user_permission=None
            )
        
        try:
            # Decodificar el ID si es un ID de GraphQL Relay
            actual_user_id = user_id
            if user_id.startswith('VXNlclR5cGU6') or not '-' in user_id:
                # Es un ID codificado de GraphQL Relay, decodificarlo
                from graphql_relay import from_global_id
                try:
                    node_type, actual_user_id = from_global_id(user_id)
                    if node_type != 'UserType':
                        return GrantUserPermission(
                            success=False,
                            message=f"ID de usuario inválido: tipo {node_type} no es UserType",
                            user_permission=None
                        )
                except Exception:
                    # Si falla la decodificación, usar el ID original
                    actual_user_id = user_id
            
            # Buscar el usuario objetivo
            target_user = User.objects.get(pk=actual_user_id)
            
            # Buscar el permiso
            permission = Permission.objects.get(pk=permission_id)
            
            # Verificar si el usuario ya tiene este permiso personalizado
            existing_permission = UserPermission.objects.filter(
                user=target_user,
                permission=permission
            ).first()
            
            if existing_permission:
                return GrantUserPermission(
                    success=False,
                    message=f"El usuario {target_user.username} ya tiene el permiso {permission.name}",
                    user_permission=existing_permission
                )
            
            # Crear el permiso personalizado
            user_permission = UserPermission.objects.create(
                user=target_user,
                permission=permission,
                permission_type='GRANTED',
                reason=reason or f"Otorgado por {user.username}",
                expires_at=timezone.now() + timedelta(days=365)  # 1 año por defecto
            )
            
            return GrantUserPermission(
                success=True,
                message=f"Permiso {permission.name} otorgado a {target_user.username} exitosamente",
                user_permission=user_permission
            )
            
        except User.DoesNotExist:
            return GrantUserPermission(
                success=False,
                message=f"Usuario con ID {user_id} no encontrado",
                user_permission=None
            )
        except Permission.DoesNotExist:
            return GrantUserPermission(
                success=False,
                message=f"Permiso con ID {permission_id} no encontrado",
                user_permission=None
            )
        except Exception as e:
            return GrantUserPermission(
                success=False,
                message=f"Error al otorgar permiso: {str(e)}",
                user_permission=None
            )


class RevokeUserPermission(graphene.Mutation):
    """Revoca un permiso personalizado de un usuario."""
    
    class Arguments:
        user_id = graphene.ID(required=True)
        permission_id = graphene.ID(required=True)
        reason = graphene.String()
    
    success = graphene.Boolean()
    message = graphene.String()
    user_permission = graphene.Field(UserPermissionType)
    
    @staticmethod
    @login_required
    def mutate(root, info, user_id, permission_id, reason=None):
        user = info.context.user
        
        # Solo administradores pueden revocar permisos
        if user.role != 'ADMINISTRADOR':
            return RevokeUserPermission(
                success=False,
                message="No tienes permisos para revocar permisos de usuarios",
                user_permission=None
            )
        
        try:
            # Decodificar el ID si es un ID de GraphQL Relay
            actual_user_id = user_id
            if user_id.startswith('VXNlclR5cGU6') or not '-' in user_id:
                # Es un ID codificado de GraphQL Relay, decodificarlo
                from graphql_relay import from_global_id
                try:
                    node_type, actual_user_id = from_global_id(user_id)
                    if node_type != 'UserType':
                        return RevokeUserPermission(
                            success=False,
                            message=f"ID de usuario inválido: tipo {node_type} no es UserType",
                            user_permission=None
                        )
                except Exception:
                    # Si falla la decodificación, usar el ID original
                    actual_user_id = user_id
            
            # Buscar el usuario objetivo
            target_user = User.objects.get(pk=actual_user_id)
            
            # Buscar el permiso
            permission = Permission.objects.get(pk=permission_id)
            
            # Buscar el permiso personalizado del usuario
            user_permission = UserPermission.objects.filter(
                user=target_user,
                permission=permission
            ).first()
            
            if not user_permission:
                return RevokeUserPermission(
                    success=False,
                    message=f"El usuario {target_user.username} no tiene el permiso personalizado {permission.name}",
                    user_permission=None
                )
            
            # Si es GRANTED, lo cambiamos a REVOKED
            # Si es REVOKED, lo eliminamos
            if user_permission.permission_type == 'GRANTED':
                user_permission.permission_type = 'REVOKED'
                user_permission.reason = reason or f"Revocado por {user.username}"
                user_permission.save()
                
                return RevokeUserPermission(
                    success=True,
                    message=f"Permiso {permission.name} revocado a {target_user.username} exitosamente",
                    user_permission=user_permission
                )
            else:
                # Ya está revocado, lo eliminamos
                user_permission.delete()
                
                return RevokeUserPermission(
                    success=True,
                    message=f"Permiso {permission.name} eliminado completamente de {target_user.username}",
                    user_permission=None
                )
            
        except User.DoesNotExist:
            return RevokeUserPermission(
                success=False,
                message=f"Usuario con ID {user_id} no encontrado",
                user_permission=None
            )
        except Permission.DoesNotExist:
            return RevokeUserPermission(
                success=False,
                message=f"Permiso con ID {permission_id} no encontrado",
                user_permission=None
            )
        except Exception as e:
            return RevokeUserPermission(
                success=False,
                message=f"Error al revocar permiso: {str(e)}",
                user_permission=None
            )


# ===== MUTATIONS DE PERMISOS =====

class CreatePermission(graphene.Mutation):
    """Crea un nuevo permiso (solo ADMINISTRADOR)."""
    
    class Arguments:
        input = PermissionInput(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    permission = graphene.Field(PermissionType)
    
    @staticmethod
    @login_required
    def mutate(root, info, input):
        user = info.context.user
        
        # Verificar que sea administrador
        if not user.is_administrador and not user.is_superuser:
            return CreatePermission(
                success=False,
                message='Solo administradores pueden crear permisos'
            )
        
        # Verificar si ya existe
        if Permission.objects.filter(code=input.code).exists():
            return CreatePermission(
                success=False,
                message=f'Ya existe un permiso con código "{input.code}"'
            )
        
        # Crear permiso
        permission = Permission.objects.create(
            code=input.code,
            name=input.name,
            description=input.get('description'),
            module=input.get('module')
        )
        
        return CreatePermission(
            success=True,
            message='Permiso creado exitosamente',
            permission=permission
        )


class UpdatePermission(graphene.Mutation):
    """Actualiza un permiso existente (solo ADMINISTRADOR)."""
    
    class Arguments:
        id = graphene.ID(required=True)
        input = PermissionInput(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    permission = graphene.Field(PermissionType)
    
    @staticmethod
    @login_required
    def mutate(root, info, id, input):
        user = info.context.user
        
        if not user.is_administrador and not user.is_superuser:
            return UpdatePermission(
                success=False,
                message='Solo administradores pueden actualizar permisos'
            )
        
        try:
            permission = Permission.objects.get(pk=id)
        except Permission.DoesNotExist:
            return UpdatePermission(
                success=False,
                message='Permiso no encontrado'
            )
        
        permission.name = input.name
        permission.description = input.get('description')
        permission.module = input.get('module')
        permission.save()
        
        return UpdatePermission(
            success=True,
            message='Permiso actualizado exitosamente',
            permission=permission
        )


# ===== MUTATIONS DE ROLES =====

class CreateRole(graphene.Mutation):
    """Crea un nuevo rol con permisos (solo ADMINISTRADOR)."""
    
    class Arguments:
        input = RoleInput(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    role = graphene.Field(RoleType)
    
    @staticmethod
    @login_required
    def mutate(root, info, input):
        user = info.context.user
        
        if not user.is_administrador and not user.is_superuser:
            return CreateRole(
                success=False,
                message='Solo administradores pueden crear roles'
            )
        
        if Role.objects.filter(code=input.code).exists():
            return CreateRole(
                success=False,
                message=f'Ya existe un rol con código "{input.code}"'
            )
        
        # Crear rol
        role = Role.objects.create(
            code=input.code,
            name=input.name,
            description=input.get('description')
        )
        
        # Asignar permisos si se proporcionaron
        if input.get('permission_ids'):
            for perm_id in input.permission_ids:
                try:
                    perm = Permission.objects.get(pk=perm_id)
                    RolePermission.objects.create(
                        role=role,
                        permission=perm,
                        granted_by=user
                    )
                except Permission.DoesNotExist:
                    pass
        
        return CreateRole(
            success=True,
            message='Rol creado exitosamente',
            role=role
        )


class UpdateRole(graphene.Mutation):
    """Actualiza un rol existente (solo ADMINISTRADOR)."""
    
    class Arguments:
        id = graphene.ID(required=True)
        input = RoleInput(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    role = graphene.Field(RoleType)
    
    @staticmethod
    @login_required
    def mutate(root, info, id, input):
        user = info.context.user
        
        if not user.is_administrador and not user.is_superuser:
            return UpdateRole(
                success=False,
                message='Solo administradores pueden actualizar roles'
            )
        
        try:
            role = Role.objects.get(pk=id)
        except Role.DoesNotExist:
            return UpdateRole(
                success=False,
                message='Rol no encontrado'
            )
        
        # No permitir modificar roles del sistema
        if role.is_system:
            return UpdateRole(
                success=False,
                message='No se pueden modificar roles del sistema'
            )
        
        role.name = input.name
        role.description = input.get('description')
        role.save()
        
        # Actualizar permisos si se proporcionaron
        if input.get('permission_ids') is not None:
            # Eliminar permisos actuales
            RolePermission.objects.filter(role=role).delete()
            
            # Agregar nuevos permisos
            for perm_id in input.permission_ids:
                try:
                    perm = Permission.objects.get(pk=perm_id)
                    RolePermission.objects.create(
                        role=role,
                        permission=perm,
                        granted_by=user
                    )
                except Permission.DoesNotExist:
                    pass
        
        return UpdateRole(
            success=True,
            message='Rol actualizado exitosamente',
            role=role
        )


class AssignRoleToUser(graphene.Mutation):
    """Asigna un rol a un usuario (solo ADMINISTRADOR)."""
    
    class Arguments:
        user_id = graphene.ID(required=True)
        role_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    user = graphene.Field(UserType)
    
    @staticmethod
    @login_required
    def mutate(root, info, user_id, role_id):
        admin_user = info.context.user
        
        if not admin_user.is_administrador and not admin_user.is_superuser:
            return AssignRoleToUser(
                success=False,
                message='Solo administradores pueden asignar roles'
            )
        
        try:
            target_user = User.objects.get(pk=user_id)
            role = Role.objects.get(pk=role_id)
        except (User.DoesNotExist, Role.DoesNotExist):
            return AssignRoleToUser(
                success=False,
                message='Usuario o rol no encontrado'
            )
        
        target_user.role_obj = role
        target_user.save(update_fields=['role_obj'])
        
        return AssignRoleToUser(
            success=True,
            message=f'Rol "{role.name}" asignado exitosamente',
            user=target_user
        )


# ===== MUTATIONS DE PERMISOS PERSONALIZADOS =====

class GrantUserPermission(graphene.Mutation):
    """Otorga un permiso adicional a un usuario (solo ADMINISTRADOR)."""
    
    class Arguments:
        user_id = graphene.ID(required=True)
        permission_id = graphene.ID(required=True)
        reason = graphene.String()
        expires_in_days = graphene.Int()
    
    success = graphene.Boolean()
    message = graphene.String()
    user_permission = graphene.Field(UserPermissionType)
    
    @staticmethod
    @login_required
    def mutate(root, info, user_id, permission_id, reason=None, expires_in_days=None):
        admin_user = info.context.user
        
        if not admin_user.is_administrador and not admin_user.is_superuser:
            return GrantUserPermission(
                success=False,
                message='Solo administradores pueden otorgar permisos'
            )
        
        try:
            target_user = User.objects.get(pk=user_id)
            permission = Permission.objects.get(pk=permission_id)
        except (User.DoesNotExist, Permission.DoesNotExist):
            return GrantUserPermission(
                success=False,
                message='Usuario o permiso no encontrado'
            )
        
        # Calcular expiración
        expires_at = None
        if expires_in_days:
            expires_at = timezone.now() + timedelta(days=expires_in_days)
        
        # Crear o actualizar permiso personalizado
        user_perm, created = UserPermission.objects.update_or_create(
            user=target_user,
            permission=permission,
            defaults={
                'permission_type': 'GRANT',
                'granted_by': admin_user,
                'reason': reason,
                'expires_at': expires_at
            }
        )
        
        return GrantUserPermission(
            success=True,
            message='Permiso otorgado exitosamente',
            user_permission=user_perm
        )


class RevokeUserPermission(graphene.Mutation):
    """Revoca un permiso de un usuario (solo ADMINISTRADOR)."""
    
    class Arguments:
        user_id = graphene.ID(required=True)
        permission_id = graphene.ID(required=True)
        reason = graphene.String()
    
    success = graphene.Boolean()
    message = graphene.String()
    user_permission = graphene.Field(UserPermissionType)
    
    @staticmethod
    @login_required
    def mutate(root, info, user_id, permission_id, reason=None):
        admin_user = info.context.user
        
        if not admin_user.is_administrador and not admin_user.is_superuser:
            return RevokeUserPermission(
                success=False,
                message='Solo administradores pueden revocar permisos'
            )
        
        try:
            target_user = User.objects.get(pk=user_id)
            permission = Permission.objects.get(pk=permission_id)
        except (User.DoesNotExist, Permission.DoesNotExist):
            return RevokeUserPermission(
                success=False,
                message='Usuario o permiso no encontrado'
            )
        
        # Crear o actualizar para revocar
        user_perm, created = UserPermission.objects.update_or_create(
            user=target_user,
            permission=permission,
            defaults={
                'permission_type': 'REVOKE',
                'granted_by': admin_user,
                'reason': reason
            }
        )
        
        return RevokeUserPermission(
            success=True,
            message='Permiso revocado exitosamente',
            user_permission=user_perm
        )


class RemoveUserPermission(graphene.Mutation):
    """Elimina un permiso personalizado de un usuario (solo ADMINISTRADOR)."""
    
    class Arguments:
        user_permission_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    @staticmethod
    @login_required
    def mutate(root, info, user_permission_id):
        admin_user = info.context.user
        
        if not admin_user.is_administrador and not admin_user.is_superuser:
            return RemoveUserPermission(
                success=False,
                message='Solo administradores pueden eliminar permisos personalizados'
            )
        
        try:
            user_perm = UserPermission.objects.get(pk=user_permission_id)
            user_perm.delete()
        except UserPermission.DoesNotExist:
            return RemoveUserPermission(
                success=False,
                message='Permiso personalizado no encontrado'
            )
        
        return RemoveUserPermission(
            success=True,
            message='Permiso personalizado eliminado'
        )
