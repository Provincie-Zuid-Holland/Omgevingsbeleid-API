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
    module_can_complete_module = "module_can_complete_module"
    module_can_patch_module_status = "module_can_patch_module_status"
    module_can_add_new_object_to_module = "module_can_add_new_object_to_module"
    module_can_add_existing_object_to_module = "module_can_add_existing_object_to_module"
    module_can_edit_module_object_context = "module_can_edit_module_object_context"
    module_can_remove_object_from_module = "module_can_remove_object_from_module"
    module_can_patch_object_in_module = "module_can_patch_object_in_module"

    # Publication
    publication_can_create_publication_template = "publication_can_create_publication_template"
    publication_can_edit_publication_template = "publication_can_edit_publication_template"
    publication_can_view_publication_template = "publication_can_view_publication_template"

    publication_can_create_publication_environment = "publication_can_create_publication_environment"
    publication_can_edit_publication_environment = "publication_can_edit_publication_environment"
    publication_can_view_publication_environment = "publication_can_view_publication_environment"

    publication_can_create_publication_aoj = "publication_can_create_publication_aoj"
    publication_can_view_publication_aoj = "publication_can_view_publication_aoj"

    publication_can_create_publication_act = "publication_can_create_publication_act"
    publication_can_edit_publication_act = "publication_can_edit_publication_act"
    publication_can_close_publication_act = "publication_can_close_publication_act"
    publication_can_view_publication_act = "publication_can_view_publication_act"

    publication_can_create_publication = "publication_can_create_publication"
    publication_can_edit_publication = "publication_can_edit_publication"
    publication_can_view_publication = "publication_can_view_publication"

    publication_can_create_publication_version = "publication_can_create_publication_version"
    publication_can_edit_publication_version = "publication_can_edit_publication_version"
    publication_can_view_publication_version = "publication_can_view_publication_version"
    publication_can_delete_publication_version_attachment = "publication_can_delete_publication_version_attachment"

    publication_can_create_publication_act_package = "publication_can_create_publication_act_package"
    publication_can_view_publication_act_package = "publication_can_view_publication_act_package"
    publication_can_download_publication_act_package = "publication_can_download_publication_act_package"

    publication_can_upload_publication_act_package_report = "publication_can_upload_publication_act_package_report"
    publication_can_view_publication_act_package_report = "publication_can_view_publication_act_package_report"
    publication_can_download_publication_act_package_report = "publication_can_download_publication_act_package_report"

    publication_can_create_publication_announcement = "publication_can_create_publication_announcement"
    publication_can_edit_publication_announcement = "publication_can_edit_publication_announcement"
    publication_can_view_publication_announcement = "publication_can_view_publication_announcement"

    publication_can_create_publication_announcement_package = "publication_can_create_publication_announcement_package"
    publication_can_view_publication_announcement_package = "publication_can_view_publication_announcement_package"
    publication_can_download_publication_announcement_package = (
        "publication_can_download_publication_announcement_package"
    )

    publication_can_upload_publication_announcement_package_report = (
        "publication_can_upload_publication_announcement_package_report"
    )
    publication_can_view_publication_announcement_package_report = (
        "publication_can_view_publication_announcement_package_report"
    )
    publication_can_download_publication_announcement_package_report = (
        "publication_can_download_publication_announcement_package_report"
    )
