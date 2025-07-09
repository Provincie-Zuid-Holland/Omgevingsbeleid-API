import uuid
from typing import Dict, List, Optional, Set

from fastapi import HTTPException, status

from app.core.services.main_config import MainConfig
from app.core.tables.users import UsersTable


class PermissionService:
    def __init__(self, main_config: MainConfig):
        self._permissions_per_role: Dict[str, Set[str]] = {}

        main_config_dict: dict = main_config.get_main_config()
        config_permissions: Dict[str, List[str]] = main_config_dict.get("users_permissions", {})
        for role, permissions in config_permissions.items():
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
