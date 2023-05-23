from typing import Dict, List, Set
import uuid

from fastapi import HTTPException

from app.extensions.users.db.tables import UsersTable


class PermissionService:
    def __init__(self):
        self._permissions_per_role: Dict[str, Set[str]] = {}

    def overwrite_role(self, role: str, permissions: List[str]):
        self._permissions_per_role[role] = set(permissions)

    def has_permission(self, permission: str, user: UsersTable) -> bool:
        permissions: Set[str] = self._permissions_per_role.get(user.Rol, set([]))
        return permission in permissions

    def guard_valid_user(
        self,
        permission: str,
        user: UsersTable,
        whitelisted_uuids: List[uuid.UUID] = [],
    ):
        if user.UUID in whitelisted_uuids:
            return

        if not self.has_permission(permission, user):
            raise HTTPException(status_code=401, detail="Invalid user role")


main_permission_service = PermissionService()
