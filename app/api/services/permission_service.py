import uuid
from typing import Dict, List, Optional, Set

from fastapi import HTTPException, status

from app.core.tables.users import UsersTable


class PermissionService:
    def __init__(self):
        self._permissions_per_role: Dict[str, Set[str]] = {}

    def overwrite_role(self, role: str, permissions: List[str]):
        self._permissions_per_role[role] = set(permissions)

    def has_permission(self, permission: str, user: UsersTable) -> bool:
        role: Optional[str] = user.Rol
        if role is None:
            return False

        permissions: Set[str] = self._permissions_per_role.get(role, set())
        return permission in permissions

    def guard_valid_user(
        self,
        permission: str,
        user: Optional[UsersTable],
        whitelisted_uuids: List[Optional[uuid.UUID]] = [],
    ):
        if user is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid user role")

        if user.UUID in whitelisted_uuids:
            return

        if not self.has_permission(permission, user):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid user role")
