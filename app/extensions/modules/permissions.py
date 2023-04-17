from enum import Enum
from typing import List, Optional
import uuid

from fastapi import HTTPException
from app.extensions.modules.db.tables import ModuleStatusHistoryTable, ModuleTable
from app.extensions.modules.models.models import AllModuleStatusCode
from app.extensions.modules.repository.module_status_repository import (
    ModuleStatusRepository,
)

from app.extensions.users.db.tables import UsersTable
from app.extensions.users.permission_service import PermissionService


class ModulesPermissions(str, Enum):
    can_create_module = "can_create_module"
    can_edit_module = "can_edit_module"
    can_patch_module_status = "can_patch_module_status"
    can_add_new_object_to_module = "can_add_new_object_to_module"
    can_add_existing_object_to_module = "can_add_existing_object_to_module"
    can_edit_module_object_context = "can_edit_module_object_context"
    can_remove_object_from_module = "can_remove_object_from_module"
    can_patch_object_in_module = "can_patch_object_in_module"


def guard_user_is_module_manager(user: UsersTable, module: ModuleTable):
    if not module.is_manager(user.UUID):
        raise HTTPException(401, "You are not allowed to modify this module")


def guard_module_is_locked(module: ModuleTable):
    if not module.Temporary_Locked:
        raise HTTPException(
            400, "The module's status can only be changed when it is locked"
        )


def guard_module_not_locked(module: ModuleTable):
    if module.Temporary_Locked:
        raise HTTPException(status_code=400, detail="The module is locked")


def guard_module_not_activated(module: ModuleTable):
    if module.Activated:
        raise HTTPException(400, "The module is already activated")


def guard_valid_user(
    permission_service: PermissionService,
    permission: str,
    user: UsersTable,
    module: ModuleTable,
    whitelisted_uuids: List[uuid.UUID] = [],
):
    if module.is_manager(user.UUID):
        return

    if user.UUID in whitelisted_uuids:
        return

    if not permission_service.has_permission(permission, user):
        raise HTTPException(status_code=401, detail="Invalid user role")


def guard_status_must_be_vastgesteld(
    module_status_repository: ModuleStatusRepository, module: ModuleTable
):
    status: Optional[
        ModuleStatusHistoryTable
    ] = module_status_repository.get_latest_for_module(module.Module_ID)
    if status is None:
        raise HTTPException(400, "Deze module heeft geen status")
    if status.Status != AllModuleStatusCode.Vastgesteld:
        raise HTTPException(
            400, "Alleen modules met status Vastgesteld kunnen worden afgesloten"
        )
