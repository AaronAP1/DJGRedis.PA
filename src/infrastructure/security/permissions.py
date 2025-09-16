from rest_framework import permissions


class IsAdminOrCoordinatorOrSecretary(permissions.BasePermission):
    """Permite acceso solo a ADMINISTRADOR, COORDINADOR o SECRETARIA."""

    allowed_roles = {"ADMINISTRADOR", "COORDINADOR", "SECRETARIA"}

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        role = getattr(user, 'role', None)
        return role in self.allowed_roles


class IsAdminOnly(permissions.BasePermission):
    """Permite acceso solo a ADMINISTRADOR."""

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        return bool(user and user.is_authenticated and getattr(user, 'role', None) == 'ADMINISTRADOR')
