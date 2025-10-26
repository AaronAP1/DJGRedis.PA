from typing import Optional
from django.db import connection


def _role_has_permission_from_json(role, permission_code: str) -> bool:
    """Check role.permisos JSON structure for permission like 'module.action'.

    role: Role model instance (expected to have .permisos dict)
    permission_code: 'module.action' or 'module' (for all)
    """
    try:
        permisos = getattr(role, 'permisos', {}) or {}
    except Exception:
        return False

    # If permisos contains {'all': True} -> full access
    if permisos.get('all') is True:
        return True

    # Split permission code
    if '.' in permission_code:
        module, action = permission_code.split('.', 1)
        module_perms = permisos.get(module, [])
        return isinstance(module_perms, list) and action in module_perms

    # If only module given, check presence
    return bool(permisos.get(permission_code))


def _role_has_permission_from_tables(role_id: int, permission_code: str) -> bool:
    """Fallback: check upeu_permiso and upeu_rol_permiso tables using raw SQL.

    This avoids requiring Django models for these optional tables.
    """
    if not role_id:
        return False

    with connection.cursor() as cur:
        # Ensure tables exist (simple, tolerant check)
        cur.execute("SELECT to_regclass('public.upeu_permiso')")
        perm_table = cur.fetchone()[0]
        if not perm_table:
            return False

        # Query mapping
        cur.execute(
            """
            SELECT 1
            FROM upeu_permiso p
            JOIN upeu_rol_permiso rp ON rp.permiso_id = p.id
            WHERE rp.rol_id = %s AND p.codigo = %s
            LIMIT 1
            """,
            [role_id, permission_code]
        )
        return cur.fetchone() is not None


def has_permission(user, permission_code: str) -> bool:
    """Public helper to check whether a user has a named permission.

    Strategy:
    1. If user or not authenticated -> False
    2. If user's role (Role instance) has permisos JSON and matches -> True
    3. Else, fallback to checking permission mapping tables (upeu_permiso + upeu_rol_permiso)

    permission_code: 'module.action' (e.g., 'practices.view')
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return False

    # Superuser shortcut: if Django user has is_superuser -> allow
    if getattr(user, 'is_superuser', False):
        return True

    # Try to get role object (we store rol_id FK and role property alias)
    role_obj = getattr(user, 'rol', None) or getattr(user, 'role', None)

    # If role_obj is an integer id, try to get role via user.rol_id or rol_id
    if role_obj is None:
        # Some user objects store rol_id
        role_id = getattr(user, 'rol_id', None) or getattr(user, 'role_id', None)
    else:
        # If role_obj is a model instance with permisos
        if _role_has_permission_from_json(role_obj, permission_code):
            return True
        role_id = getattr(role_obj, 'id', None)

    # Fallback: check tables mapping
    try:
        return _role_has_permission_from_tables(role_id, permission_code)
    except Exception:
        return False
