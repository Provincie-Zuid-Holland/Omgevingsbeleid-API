from enum import Enum


class Permissions(str, Enum):
    # Object

    # Object Static
    can_patch_object_static = "can_patch_object_static"

    # Atemporal Object
    atemporal_can_create_object = "atemporal_can_create_object"
    atemporal_can_edit_object = "atemporal_can_edit_object"
    atemporal_can_delete_object = "atemporal_can_delete_object"

    # Module
    module_can_create_module = "module_can_create_module"
    module_can_close_module = "module_can_close_module"
    module_can_edit_module = "module_can_edit_module"
    module_can_activate_module = "module_can_activate_module"
    module_can_patch_module_status = "module_can_patch_module_status"
    module_can_add_new_object_to_module = "module_can_add_new_object_to_module"
    module_can_add_existing_object_to_module = "module_can_add_existing_object_to_module"
    module_can_edit_module_object_context = "module_can_edit_module_object_context"
    module_can_remove_object_from_module = "module_can_remove_object_from_module"
    module_can_patch_object_in_module = "module_can_patch_object_in_module"
