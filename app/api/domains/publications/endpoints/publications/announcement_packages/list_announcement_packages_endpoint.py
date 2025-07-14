import uuid
from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_optional_sorted_pagination
from app.api.domains.publications.repository.publication_announcement_package_repository import (
    PublicationAnnouncementPackageRepository,
)
from app.api.domains.publications.types.enums import PackageType
from app.api.domains.publications.types.models import PublicationPackage
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.endpoint import BaseEndpointContext
from app.api.permissions import Permissions
from app.api.utils.pagination import OptionalSortedPagination, OrderConfig, PagedResponse, Sort, SortedPagination
from app.core.tables.users import UsersTable


class ListAnnouncementPackagesEndpointContext(BaseEndpointContext):
    order_config: OrderConfig


@inject
def get_list_announcement_packages_endpoint(
    optional_pagination: Annotated[OptionalSortedPagination, Depends(depends_optional_sorted_pagination)],
    session: Annotated[Session, Depends(depends_db_session)],
    package_repository: Annotated[
        PublicationAnnouncementPackageRepository,
        Depends(Provide[ApiContainer.publication.announcement_package_repository]),
    ],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_announcement_package,
            )
        ),
    ],
    context: Annotated[ListAnnouncementPackagesEndpointContext, Depends()],
    announcement_uuid: Optional[uuid.UUID] = None,
    package_type: Optional[PackageType] = None,
) -> PagedResponse[PublicationPackage]:
    sort: Sort = context.order_config.get_sort(optional_pagination.sort)
    pagination: SortedPagination = optional_pagination.with_sort(sort)

    paginated_result = package_repository.get_with_filters(
        session=session,
        announcement_uuid=announcement_uuid,
        package_type=package_type,
        pagination=pagination,
    )

    results = [PublicationPackage.model_validate(r) for r in paginated_result.items]

    return PagedResponse[PublicationPackage](
        total=paginated_result.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=results,
    )
