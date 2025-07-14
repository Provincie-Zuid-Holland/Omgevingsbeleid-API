from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_simple_pagination
from app.api.domains.publications.repository.publication_template_repository import PublicationTemplateRepository
from app.api.domains.publications.types.enums import DocumentType
from app.api.domains.publications.types.models import PublicationTemplate
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.utils.pagination import PagedResponse, SimplePagination
from app.core.tables.users import UsersTable


@inject
def get_list_templates_endpoint(
    is_active: Annotated[Optional[bool], None],
    document_type: Annotated[Optional[DocumentType], None],
    pagination: Annotated[SimplePagination, Depends(depends_simple_pagination)],
    session: Annotated[Session, Depends(depends_db_session)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_template,
            )
        ),
    ],
    template_repository: Annotated[
        PublicationTemplateRepository, Depends(Provide[ApiContainer.publication.template_repository])
    ],
) -> PagedResponse[PublicationTemplate]:
    paginated_result = template_repository.get_with_filters(
        session=session,
        is_active=is_active,
        document_type=document_type,
        offset=pagination.offset,
        limit=pagination.limit,
    )

    results = [PublicationTemplate.model_validate(r) for r in paginated_result.items]

    return PagedResponse[PublicationTemplate](
        total=paginated_result.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=results,
    )
