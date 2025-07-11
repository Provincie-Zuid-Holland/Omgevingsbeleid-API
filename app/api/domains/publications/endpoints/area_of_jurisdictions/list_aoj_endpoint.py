from typing import Annotated, List

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_simple_pagination
from app.api.domains.publications.repository.publication_aoj_repository import PublicationAOJRepository
from app.api.domains.publications.types.models import PublicationAOJ
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.utils.pagination import PagedResponse, SimplePagination
from app.core.tables.users import UsersTable


@inject
def get_list_aoj_endpoint(
    pagination: Annotated[SimplePagination, Depends(depends_simple_pagination)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_aoj,
            )
        ),
    ],
    session: Annotated[Session, Depends(depends_db_session)],
    aoj_repository: Annotated[PublicationAOJRepository, Depends(Provide[ApiContainer.publication.aoj_repository])],
) -> PagedResponse[PublicationAOJ]:
    paginated_result = aoj_repository.get_with_filters(
        session=session,
        offset=pagination.offset,
        limit=pagination.limit,
    )

    results: List[PublicationAOJ] = [PublicationAOJ.model_validate(r) for r in paginated_result.items]

    return PagedResponse[PublicationAOJ](
        total=paginated_result.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=results,
    )
