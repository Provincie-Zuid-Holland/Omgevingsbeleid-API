from datetime import datetime
from typing import Annotated, Optional
import uuid

from fastapi import Depends
from pydantic import BaseModel, ConfigDict

from app.api.domains.publications.dependencies import depends_publication_act_package
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationActPackageTable
from app.core.tables.users import UsersTable


class PublicationActPackageDetailResponse(BaseModel):
    UUID: uuid.UUID
    Package_Type: str
    Report_Status: str
    Delivery_ID: str

    Publication_Version_UUID: uuid.UUID
    Bill_Version_UUID: Optional[uuid.UUID]
    Act_Version_UUID: Optional[uuid.UUID]
    Zip_UUID: uuid.UUID
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


def get_detail_act_package_endpoint(
    act_package: Annotated[PublicationActPackageTable, Depends(depends_publication_act_package)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_act_package,
            )
        ),
    ],
) -> PublicationActPackageDetailResponse:
    module = act_package.Publication_Version.Publication.Module
    module_status = act_package.Publication_Version.Module_Status
    environment = act_package.Publication_Version.Publication.Environment

    result = PublicationActPackageDetailResponse(
        UUID=act_package.UUID,
        Package_Type=act_package.Package_Type,
        Report_Status=act_package.Report_Status,
        Delivery_ID=act_package.Delivery_ID,
        Publication_Version_UUID=act_package.Publication_Version_UUID,
        Bill_Version_UUID=act_package.Bill_Version_UUID,
        Act_Version_UUID=act_package.Act_Version_UUID,
        Zip_UUID=act_package.Zip_UUID,
        Created_Environment_State_UUID=act_package.Created_Environment_State_UUID,
        Used_Environment_State_UUID=act_package.Used_Environment_State_UUID,
        Created_Date=act_package.Created_Date,
        Modified_Date=act_package.Modified_Date,
        Created_By_UUID=act_package.Created_By_UUID,
        Modified_By_UUID=act_package.Modified_By_UUID,
        Module_ID=module.Module_ID,
        Module_Title=module.Title,
        Module_Status_ID=module_status.ID,
        Module_Status_Status=module_status.Status,
        Environment_UUID=environment.UUID,
        Environment_Title=environment.Title,
    )

    return result
