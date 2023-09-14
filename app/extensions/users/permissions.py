from enum import Enum


class UserManagementPermissions(str, Enum):
    can_create_user = "can_create_user"
    can_edit_user = "can_edit_user"
    can_reset_user_password = "can_reset_user_password"  # nosec
