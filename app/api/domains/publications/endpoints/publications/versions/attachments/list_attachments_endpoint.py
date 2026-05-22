from typing import Annotated, List

from dependency_injector.wiring import inject, Provide
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.publications.dependencies import depends_publication_version
from app.api.domains.publications.repository import PublicationVersionAttachmentRepository
from app.api.domains.publications.types.models import AttachmentShort
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationVersionTable, PublicationVersionAttachmentTable
from app.core.tables.users import UsersTable


@inject
def get_list_attachments_endpoint(
    version: Annotated[PublicationVersionTable, Depends(depends_publication_version)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_version,
            )
        ),
    ],
    publication_version_attachment_repository: Annotated[
        PublicationVersionAttachmentRepository, Depends(Provide[ApiContainer.publication.version_attachment_repository])
    ],
    session: Annotated[Session, Depends(depends_db_session)],
) -> List[AttachmentShort]:
    attachments: List[PublicationVersionAttachmentTable] = (
        publication_version_attachment_repository.get_by_version_uuid(session, version.UUID)
    )
    response: List[AttachmentShort] = [AttachmentShort.model_validate(r) for r in attachments]
    return response
