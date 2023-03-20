from typing import Dict, List, Set

from app.extensions.users.db.tables import UsersTable


class PermissionService:
    def __init__(self):
        self._permissions_per_role: Dict[str, Set[str]] = {}

    def overwrite_role(self, role: str, permissions: List[str]):
        self._permissions_per_role[role] = set(permissions)

    def has_permission(self, permission: str, user: UsersTable) -> bool:
        permissions: Set[str] = self._permissions_per_role.get(user.Rol, set([]))
        return permission in permissions


main_permission_service = PermissionService()
