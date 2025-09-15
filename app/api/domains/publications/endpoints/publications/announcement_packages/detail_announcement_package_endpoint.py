from datetime import datetime
from typing import Annotated, Optional
import uuid

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
    Doc_Version_UUID: Optional[uuid.UUID]
    Zip: PackageZipShort
    Created_Environment_State_UUID: Optional[uuid.UUID]
    Used_Environment_State_UUID: Optional[uuid.UUID]

    Created_Date: datetime
    Modified_Date: datetime
    Created_By_UUID: uuid.UUID
    Modified_By_UUID: uuid.UUID

    Module_ID: int
    Module_Title: str
    Module_Status_ID: int
    Module_Status_Status: str
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
    act_package: PublicationActPackageTable = announcement_package.Announcement.Act_Package
    publication_version: PublicationVersionTable = act_package.Publication_Version
    module: ModuleTable = publication_version.Publication.Module
    module_status: ModuleStatusHistoryTable = publication_version.Module_Status
    environment: PublicationEnvironmentTable = publication_version.Publication.Environment
    zip: PackageZipShort = PackageZipShort.model_validate(announcement_package.Zip)

    result = PublicationAnnouncementPackageDetailResponse(
        UUID=announcement_package.UUID,
        Package_Type=announcement_package.Package_Type,
        Report_Status=announcement_package.Report_Status,
        Delivery_ID=announcement_package.Delivery_ID,
        Document_Type=publication_version.Publication.Document_Type,
        Announcement_UUID=announcement_package.Announcement_UUID,
        Doc_Version_UUID=announcement_package.Doc_Version_UUID,
        Zip=zip,
        Created_Environment_State_UUID=announcement_package.Created_Environment_State_UUID,
        Used_Environment_State_UUID=announcement_package.Used_Environment_State_UUID,
        Created_Date=announcement_package.Created_Date,
        Modified_Date=announcement_package.Modified_Date,
        Created_By_UUID=announcement_package.Created_By_UUID,
        Modified_By_UUID=announcement_package.Modified_By_UUID,
        Module_ID=module.Module_ID,
        Module_Title=module.Title,
        Module_Status_ID=module_status.ID,
        Module_Status_Status=module_status.Status,
        Environment_UUID=environment.UUID,
        Environment_Title=environment.Title,
    )

    return result
