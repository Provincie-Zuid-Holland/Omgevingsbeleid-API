from fastapi import HTTPException, status

from app.core.tables.modules import ModuleTable
from app.core.tables.users import UsersTable


def guard_user_is_module_manager(user: UsersTable, module: ModuleTable):
    if not module.is_manager(user.UUID):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "You are not allowed to modify this module")


def guard_module_is_locked(module: ModuleTable):
    if not module.Temporary_Locked:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The module's status can only be changed when it is locked")


def guard_module_not_locked(module: ModuleTable):
    if module.Temporary_Locked:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The module is locked")


def guard_module_not_activated(module: ModuleTable):
    if module.Activated:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The module is already activated")
