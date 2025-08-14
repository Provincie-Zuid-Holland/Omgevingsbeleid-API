from datetime import datetime
import uuid
from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_optional_sorted_pagination
from app.api.domains.publications.repository.publication_environment_repository import PublicationEnvironmentRepository
from app.api.domains.publications.repository.publication_act_package_repository import PublicationActPackageRepository
from app.api.domains.publications.repository.publication_announcement_package_repository import (
    PublicationAnnouncementPackageRepository,
)
from app.api.domains.publications.types.enums import DocumentType, PackageFilterType, PackageType, ReportStatusType
from app.api.domains.publications.types.filters import PublicationPackageFilters
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.endpoint import BaseEndpointContext
from app.api.permissions import Permissions
from app.api.types import Selectable
from app.api.utils.pagination import OptionalSortedPagination, OrderConfig, PagedResponse, Sort, SortedPagination
from app.core.tables.users import UsersTable


class PublicationPackageListItem(BaseModel):
    UUID: uuid.UUID
    Package_Type: str
    Report_Status: str
    Created_Date: datetime
    Document_Type: DocumentType
    Package_Category: PackageFilterType
    Module_ID: int
    Module_Title: str
    Publication_Environment_UUID: uuid.UUID
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class ListPackagesEndpointContext(BaseEndpointContext):
    order_config: OrderConfig


@inject
def get_list_packages_endpoint(
    optional_pagination: Annotated[OptionalSortedPagination, Depends(depends_optional_sorted_pagination)],
    session: Annotated[Session, Depends(depends_db_session)],
    act_package_repository: Annotated[
        PublicationActPackageRepository, Depends(Provide[ApiContainer.publication.act_package_repository])
    ],
    announcement_package_repository: Annotated[
        PublicationAnnouncementPackageRepository,
        Depends(Provide[ApiContainer.publication.announcement_package_repository]),
    ],
    environment_repo: Annotated[
        PublicationEnvironmentRepository, Depends(Provide[ApiContainer.publication.environment_repository])
    ],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_act_package,
            )
        ),
    ],
    context: Annotated[ListPackagesEndpointContext, Depends()],
    filters: Annotated[PublicationPackageFilters, Depends()],
    package_filter: Optional[PackageFilterType] = None,
) -> PagedResponse[PublicationPackageListItem]:
    if filters.environment_uuid:
        if not environment_repo.get_active(session, filters.environment_uuid):
            raise HTTPException(status_code=404, detail="Geen actieve publicatie environment gevonden")

    sort: Sort = context.order_config.get_sort(optional_pagination.sort)
    pagination = SortedPagination(offset=0, limit=20, sort=sort)

    # build appropriate queries
    query: Selectable
    if package_filter == PackageFilterType.ACT:
        query = act_package_repository.build_overview_query(filters=filters)
    elif package_filter == PackageFilterType.ANNOUNCEMENT:
        query = announcement_package_repository.build_overview_query(filters=filters)
    else:
        act_query = act_package_repository.build_overview_query(filters=filters)
        announcement_query = announcement_package_repository.build_overview_query(filters=filters)
        query = act_query.union(announcement_query)

    rows = act_package_repository.fetch_paginated_no_scalars(
        session=session,
        statement=query,
        offset=pagination.offset,
        limit=pagination.limit,
        sort=(pagination.sort.column, pagination.sort.order),
    )

    package_list = [PublicationPackageListItem.model_validate(r) for r in rows.items]

    return PagedResponse[PublicationPackageListItem](
        total=rows.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=package_list,
    )
