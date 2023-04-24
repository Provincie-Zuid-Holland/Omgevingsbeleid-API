from enum import Enum


class RegulationsPermissions(str, Enum):
    can_create_regulation = "can_create_regulation"
    can_edit_regulation = "can_edit_regulation"
    can_overwrite_object_regulations = "can_overwrite_object_regulations"
