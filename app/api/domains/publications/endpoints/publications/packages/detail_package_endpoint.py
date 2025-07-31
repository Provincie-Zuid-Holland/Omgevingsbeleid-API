from datetime import datetime
import uuid
from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.publications.repository.publication_package_repository import PublicationPackageRepository
from app.api.domains.publications.types.enums import DocumentType, PackageFilterType, PackageType, ReportStatusType
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.endpoint import BaseEndpointContext
from app.api.permissions import Permissions
from app.api.utils.pagination import OptionalSortedPagination, OrderConfig, PagedResponse, Sort, SortedPagination
from app.core.tables.users import UsersTable


class PublicationPackageDetailItem(BaseModel):
    UUID: uuid.UUID
    Package_Type: str
    Report_Status: str
    Delivery_ID: str
    Created_Date: datetime
    Created_By_UUID: uuid.UUID
    Document_Type: DocumentType
    Package_Category: PackageFilterType
    Module_ID: int
    Module_Title: str
    Publication_Environment_UUID: uuid.UUID
    Zip_UUID: uuid.UUID
    Filename: str
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


@inject
def get_detail_package_endpoint(
    session: Annotated[Session, Depends(depends_db_session)],
    package_repository: Annotated[
        PublicationPackageRepository, Depends(Provide[ApiContainer.publication.package_repository])
    ],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_act_package,
            )
        ),
    ],
    package_uuid: uuid.UUID,
) -> PublicationPackageDetailItem:
    package = package_repository.get_package_details_by_uuid(session, package_uuid)

    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")

    return PublicationPackageDetailItem.model_validate(package)
