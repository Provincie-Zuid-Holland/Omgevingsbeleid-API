from enum import Enum


class AtemporalPermissions(str, Enum):
    atemporal_can_create_object = "atemporal_can_create_object"
    atemporal_can_edit_object = "atemporal_can_edit_object"
    atemporal_can_delete_object = "atemporal_can_delete_object"
