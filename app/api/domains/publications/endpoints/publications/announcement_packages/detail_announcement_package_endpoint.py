import uuid
from datetime import datetime
from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel, ConfigDict

from app.api.domains.publications.dependencies import depends_publication_announcement_package
from app.api.domains.publications.types.models import PackageZipShort
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.modules import ModuleStatusHistoryTable, ModuleTable
from app.core.tables.publications import (
    PublicationActPackageTable,
    PublicationAnnouncementPackageTable,
    PublicationEnvironmentTable,
    PublicationVersionTable,
)
from app.core.tables.users import UsersTable


class PublicationAnnouncementPackageDetailResponse(BaseModel):
    UUID: uuid.UUID
    Package_Type: str
    Report_Status: str
    Delivery_ID: str
    Document_Type: str

    Announcement_UUID: uuid.UUID
    Doc_Version_UUID: uuid.UUID | None
    Zip: PackageZipShort
    Created_Environment_State_UUID: uuid.UUID | None
    Used_Environment_State_UUID: uuid.UUID | None

    created_date: datetime
    modified_date: datetime
    created_by_id: uuid.UUID
    modified_by_id: uuid.UUID

    module_id: int | None
    Module_Title: str | None
    Module_Status_ID: int | None
    Module_Status_Status: str | None
    Environment_UUID: uuid.UUID
    Environment_Title: str

    model_config = ConfigDict(from_attributes=True)


def get_detail_announcement_package_endpoint(
    announcement_package: Annotated[
        PublicationAnnouncementPackageTable, Depends(depends_publication_announcement_package)
    ],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_announcement_package,
            )
        ),
    ],
) -> PublicationAnnouncementPackageDetailResponse:
    act_package: PublicationActPackageTable = announcement_package.announcement.act_package
    publication_version: PublicationVersionTable = act_package.publication_version
    module: ModuleTable | None = act_package.module
    module_status: ModuleStatusHistoryTable | None = act_package.module_status
    environment: PublicationEnvironmentTable = publication_version.publication.environment
    zip: PackageZipShort = PackageZipShort.model_validate(announcement_package.zip)

    result = PublicationAnnouncementPackageDetailResponse(
        UUID=announcement_package.id,
        Package_Type=announcement_package.package_type,
        Report_Status=announcement_package.report_status,
        Delivery_ID=announcement_package.delivery_id,
        Document_Type=publication_version.publication.document_type,
        Announcement_UUID=announcement_package.announcement_id,
        Doc_Version_UUID=announcement_package.doc_version_id,
        Zip=zip,
        Created_Environment_State_UUID=announcement_package.created_environment_state_id,
        Used_Environment_State_UUID=announcement_package.used_environment_state_id,
        created_date=announcement_package.created_date,
        modified_date=announcement_package.modified_date,
        created_by_id=announcement_package.created_by_id,
        modified_by_id=announcement_package.modified_by_id,
        module_id=module.module_id if module else None,
        Module_Title=module.title if module else None,
        Module_Status_ID=module_status.id if module_status else None,
        Module_Status_Status=module_status.status if module_status else None,
        Environment_UUID=environment.id,
        Environment_Title=environment.title,
    )

    return result
