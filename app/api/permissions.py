from enum import Enum


class Permissions(str, Enum):
    # Object

    # Object Static
    can_patch_object_static = "can_patch_object_static"

    # Atemporal Object
    atemporal_can_create_object = "atemporal_can_create_object"
    atemporal_can_edit_object = "atemporal_can_edit_object"
    atemporal_can_delete_object = "atemporal_can_delete_object"
