"""
Mutations GraphQL para gestión de Roles y Permisos.
"""

import graphene
from graphql_jwt.decorators import login_required
from django.contrib.auth import get_user_model
from graphene import relay
from graphql_relay import from_global_id
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


# Utilidad: normaliza un ID aceptando tanto Global ID (Relay) como UUID crudo
def _resolve_real_id(raw_id: str) -> str:
    """Devuelve el UUID real desde un Global ID o el propio valor si ya es UUID.
    Limpia espacios y comillas tipográficas que a veces llegan desde el navegador.
    """
    try:
        s = str(raw_id or '').strip()
    except Exception:
        s = ''
    if not s:
        return ''
    
    # Eliminar comillas tipográficas u otros delimitadores extraños
    for ch in ('\u201c', '\u201d', '\u00ab', '\u00bb', '"', '"', '«', '»'):
        s = s.replace(ch, '')
    s = s.strip()
    
    if not s:
        return ''
    
    # Intentar decodificar como Global ID (Relay)
    try:
        _type, decoded = from_global_id(s)
        if decoded:
            return decoded
    except Exception:
        pass
    
    return s


# ===== MUTATIONS DE PERMISOS DE USUARIO =====
# (Las mutaciones GrantUserPermission y RevokeUserPermission se definen más abajo)


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
        
        # Decodificar ID de GraphQL Relay a UUID real
        real_id = _resolve_real_id(id)
        
        try:
            permission = Permission.objects.get(pk=real_id)
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
                    real_perm_id = _resolve_real_id(perm_id)
                    perm = Permission.objects.get(pk=real_perm_id)
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
        
        # Decodificar ID de GraphQL Relay a UUID real
        real_id = _resolve_real_id(id)
        
        try:
            role = Role.objects.get(pk=real_id)
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
                    real_perm_id = _resolve_real_id(perm_id)
                    perm = Permission.objects.get(pk=real_perm_id)
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
        
        # Decodificar IDs de GraphQL Relay a UUIDs reales
        real_user_id = _resolve_real_id(user_id)
        real_role_id = _resolve_real_id(role_id)
        
        try:
            target_user = User.objects.get(pk=real_user_id)
            role = Role.objects.get(pk=real_role_id)
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
        
        # Decodificar ID de GraphQL Relay a UUID real
        real_user_permission_id = _resolve_real_id(user_permission_id)
        
        try:
            user_perm = UserPermission.objects.get(pk=real_user_permission_id)
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
