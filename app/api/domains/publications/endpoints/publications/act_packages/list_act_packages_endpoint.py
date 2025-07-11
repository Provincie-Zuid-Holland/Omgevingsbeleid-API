import uuid
from typing import Annotated, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_optional_sorted_pagination
from app.api.domains.publications.repository.publication_act_package_repository import PublicationActPackageRepository
from app.api.domains.publications.types.enums import PackageType
from app.api.domains.publications.types.models import PublicationPackage
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.endpoint import BaseEndpointContext
from app.api.permissions import Permissions
from app.api.utils.pagination import OptionalSortedPagination, OrderConfig, PagedResponse, Sort, SortedPagination
from app.core.tables.users import UsersTable


class ListActPackagesEndpointContext(BaseEndpointContext):
    order_config: OrderConfig


@inject
def get_list_act_packages_endpoint(
    version_uuid: Annotated[Optional[uuid.UUID], None],
    package_type: Annotated[Optional[PackageType], None],
    optional_pagination: Annotated[OptionalSortedPagination, Depends(depends_optional_sorted_pagination)],
    session: Annotated[Session, Depends(depends_db_session)],
    package_repository: Annotated[
        PublicationActPackageRepository, Depends(Provide[ApiContainer.publication.act_package_repository])
    ],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_act_package,
            )
        ),
    ],
    context: Annotated[ListActPackagesEndpointContext, Depends()],
) -> PagedResponse[PublicationPackage]:
    sort: Sort = context.order_config.get_sort(optional_pagination.sort)
    pagination: SortedPagination = optional_pagination.with_sort(sort)

    paginated_result = package_repository.get_with_filters(
        session=session,
        version_uuid=version_uuid,
        package_type=package_type,
        pagination=pagination,
    )

    results: List[PublicationPackage] = [PublicationPackage.model_validate(r) for r in paginated_result.items]

    return PagedResponse[PublicationPackage](
        total=paginated_result.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=results,
    )
