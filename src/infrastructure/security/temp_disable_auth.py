"""
Mixin temporal para deshabilitar autenticación en endpoints API v2.
USO TEMPORAL - NO USAR EN PRODUCCIÓN.
"""

from rest_framework.permissions import AllowAny


class DisableAuthenticationMixin:
    """
    Mixin que deshabilita temporalmente la autenticación y permisos en ViewSets.
    ADVERTENCIA: Solo usar durante desarrollo/pruebas.
    """
    
    def get_permissions(self):
        """Sobreescribe los permisos para permitir acceso público."""
        return [AllowAny()]