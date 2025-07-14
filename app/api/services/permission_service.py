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
        # Super weird type I know
        # The inner part List[Optional[UUID]] is because we want to easily construct it without testing given values for None
        # For example: [module.Module_Manager_1_UUID, module.Module_Manager_2_UUID] where those properties can be None
        # And the outher Optional I dont like at all but setting it to = [] causes python mutable issues
        whitelisted_uuids: Optional[List[Optional[uuid.UUID]]] = None,
    ):
        if user is None or user.UUID is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid user role")

        if whitelisted_uuids and user.UUID in whitelisted_uuids:
            return

        if not self.has_permission(permission, user):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid user role")
