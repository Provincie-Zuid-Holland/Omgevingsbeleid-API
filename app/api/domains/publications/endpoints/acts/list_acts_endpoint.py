import uuid
from typing import Annotated, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_simple_pagination
from app.api.domains.publications.repository.publication_act_repository import PublicationActRepository
from app.api.domains.publications.types.enums import DocumentType, ProcedureType
from app.api.domains.publications.types.models import PublicationActShort
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.utils.pagination import PagedResponse, SimplePagination
from app.core.tables.users import UsersTable


@inject
def get_list_acts_endpoint(
    pagination: Annotated[SimplePagination, Depends(depends_simple_pagination)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_act,
            )
        ),
    ],
    session: Annotated[Session, Depends(depends_db_session)],
    act_repository: Annotated[PublicationActRepository, Depends(Provide[ApiContainer.publication.act_repository])],
    is_active: Optional[bool] = None,
    environment_uuid: Optional[uuid.UUID] = None,
    document_type: Optional[DocumentType] = None,
    procedure_type: Optional[ProcedureType] = None,
) -> PagedResponse[PublicationActShort]:
    paginated_result = act_repository.get_with_filters(
        session=session,
        is_active=is_active,
        environment_uuid=environment_uuid,
        document_type=document_type,
        procedure_type=procedure_type,
        offset=pagination.offset,
        limit=pagination.limit,
    )

    results: List[PublicationActShort] = [PublicationActShort.model_validate(r) for r in paginated_result.items]

    return PagedResponse[PublicationActShort](
        total=paginated_result.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=results,
    )
