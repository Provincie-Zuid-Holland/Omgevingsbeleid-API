from enum import Enum


class PublicationsPermissions(str, Enum):
    can_create_publication_template = "can_create_publication_template"
    can_edit_publication_template = "can_edit_publication_template"
    can_view_publication_template = "can_view_publication_template"

    can_create_publication_environment = "can_create_publication_environment"
    can_edit_publication_environment = "can_edit_publication_environment"
    can_view_publication_environment = "can_view_publication_environment"

    can_create_publication_aoj = "can_create_publication_aoj"
    can_view_publication_aoj = "can_view_publication_aoj"

    can_create_publication = "can_create_publication"
    can_edit_publication = "can_edit_publication"
    can_view_publication = "can_view_publication"

    can_create_publication_version = "can_create_publication_version"
    can_edit_publication_version = "can_edit_publication_version"
    can_view_publication_version = "can_view_publication_version"

    can_create_publication_package = "can_create_publication_package"
    can_view_publication_package = "can_view_publication_package"
    can_download_publication_package = "can_download_publication_package"