from enum import Enum


class BasePermissions(str, Enum):
    can_patch_object_static = "can_patch_object_static"
