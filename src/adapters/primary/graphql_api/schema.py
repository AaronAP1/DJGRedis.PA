"""
Schema principal de GraphQL para el sistema de gestión de prácticas profesionales.
Sistema JWT PURO.
"""

import graphene
from django.conf import settings

from .queries import Query
from .mutations import Mutation
from .jwt_mutations import JWTLogin, JWTRefresh, JWTLogout, JWTGetSessionStatus
from .permissions_mutations import (
    CreatePermission, UpdatePermission,
    CreateRole, UpdateRole, AssignRoleToUser,
    GrantUserPermission, RevokeUserPermission, RemoveUserPermission
)


class CompleteMutation(Mutation, graphene.ObjectType):
    """Mutaciones completas incluyendo JWT puro y roles/permisos."""
    
    # JWT Puro (PRINCIPAL)
    jwt_login = JWTLogin.Field()
    jwt_refresh = JWTRefresh.Field()
    jwt_logout = JWTLogout.Field()
    
    # Gestión de Roles y Permisos (ADMINISTRADOR)
    create_permission = CreatePermission.Field()
    update_permission = UpdatePermission.Field()
    create_role = CreateRole.Field()
    update_role = UpdateRole.Field()
    assign_role_to_user = AssignRoleToUser.Field()
    grant_user_permission = GrantUserPermission.Field()
    revoke_user_permission = RevokeUserPermission.Field()
    remove_user_permission = RemoveUserPermission.Field()


class CompleteQuery(Query, JWTGetSessionStatus, graphene.ObjectType):
    """Queries completas incluyendo JWT puro."""
    pass


# Schema para usar en Django settings (instancia)
schema = graphene.Schema(query=CompleteQuery, mutation=CompleteMutation)
