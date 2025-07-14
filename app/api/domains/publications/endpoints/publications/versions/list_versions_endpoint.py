import uuid
from typing import Annotated, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_simple_pagination
from app.api.domains.publications.repository.publication_version_repository import PublicationVersionRepository
from app.api.domains.publications.types.models import PublicationVersionShort
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.utils.pagination import PagedResponse, SimplePagination
from app.core.tables.users import UsersTable


@inject
def get_list_versions_endpoint(
    publication_uuid: Annotated[Optional[uuid.UUID], None],
    pagination: Annotated[SimplePagination, Depends(depends_simple_pagination)],
    session: Annotated[Session, Depends(depends_db_session)],
    version_repository: Annotated[
        PublicationVersionRepository, Depends(Provide[ApiContainer.publication.version_repository])
    ],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_version,
            )
        ),
    ],
) -> PagedResponse[PublicationVersionShort]:
    paginated_result = version_repository.get_with_filters(
        session=session,
        publication_uuid=publication_uuid,
        offset=pagination.offset,
        limit=pagination.limit,
    )

    results: List[PublicationVersionShort] = [PublicationVersionShort.model_validate(r) for r in paginated_result.items]

    return PagedResponse[PublicationVersionShort](
        total=paginated_result.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=results,
    )
