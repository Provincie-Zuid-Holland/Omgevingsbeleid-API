from typing import Annotated, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_simple_pagination
from app.api.domains.publications.repository.publication_repository import PublicationRepository
from app.api.domains.publications.types.enums import DocumentType
from app.api.domains.publications.types.models import Publication
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.utils.pagination import PagedResponse, PaginatedQueryResult, SimplePagination
from app.core.tables.users import UsersTable


@inject
def get_list_publications_endpoint(
    document_type: Annotated[Optional[DocumentType], None],
    module_id: Annotated[Optional[int], None],
    pagination: Annotated[SimplePagination, Depends(depends_simple_pagination)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication,
            )
        ),
    ],
    session: Annotated[Session, Depends(depends_db_session)],
    publication_repository: Annotated[
        PublicationRepository, Depends(Provide[ApiContainer.publication.publication_repository])
    ],
) -> PagedResponse[Publication]:
    paginated_result: PaginatedQueryResult = publication_repository.get_with_filters(
        session=session,
        document_type=document_type,
        module_id=module_id,
        offset=pagination.offset,
        limit=pagination.limit,
    )
    results: List[Publication] = [Publication.model_validate(r) for r in paginated_result.items]

    return PagedResponse[Publication](
        total=paginated_result.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=results,
    )
