from typing import Annotated, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_simple_pagination
from app.api.domains.publications.repository.publication_environment_repository import PublicationEnvironmentRepository
from app.api.domains.publications.types.models import PublicationEnvironment
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.utils.pagination import PagedResponse, SimplePagination
from app.core.tables.users import UsersTable


@inject
def get_list_environments_endpoint(
    is_active: Annotated[Optional[bool], None],
    pagination: Annotated[SimplePagination, Depends(depends_simple_pagination)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_environment,
            )
        ),
    ],
    environment_repository: Annotated[
        PublicationEnvironmentRepository, Depends(Provide[ApiContainer.publication.environment_repository])
    ],
) -> PagedResponse[PublicationEnvironment]:
    paginated_result = environment_repository.get_with_filters(
        is_active=is_active,
        offset=pagination.offset,
        limit=pagination.limit,
    )

    results: List[PublicationEnvironment] = [PublicationEnvironment.model_validate(r) for r in paginated_result.items]

    return PagedResponse[PublicationEnvironment](
        total=paginated_result.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=results,
    )
