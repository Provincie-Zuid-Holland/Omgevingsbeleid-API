from enum import Enum


class ModulesPermissions(str, Enum):
    can_create_module = "can_create_module"
    can_add_new_object_to_module = "can_add_new_object_to_module"
    can_add_existing_object_to_module = "can_add_existing_object_to_module"
    can_edit_module_object_context = "can_edit_module_object_context"
    can_remove_object_from_module = "can_remove_object_from_module"
    can_patch_object_in_module = "can_patch_object_in_module"
