from rest_framework.permissions import BasePermission
from src.infrastructure.security.permissions_service import has_permission


class HasAppPermission(BasePermission):
    """DRF permission class that checks application-level permissions.

    Usage in viewsets:
        permission_classes = [IsAuthenticated, HasAppPermission]

    Set required permission code on the view as `required_permission = 'module.action'`.
    If not set, the permission will allow only authenticated users.
    """

    def has_permission(self, request, view):
        # Default: must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        required = getattr(view, 'required_permission', None)
        if not required:
            # Authenticated users allowed if no specific permission requested
            return True

        return has_permission(request.user, required)

    def has_object_permission(self, request, view, obj):
        # If view defines a object-level permission function, call it
        obj_perm = getattr(view, 'object_permission_func', None)
        if callable(obj_perm):
            return obj_perm(request.user, obj)

        # Fallback to view-level required_permission
        return self.has_permission(request, view)
