import uuid
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.publications.dependencies import depends_publication
from app.api.domains.publications.repository.publication_template_repository import PublicationTemplateRepository
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.types import ResponseOK
from app.core.tables.publications import PublicationTable, PublicationTemplateTable
from app.core.tables.users import UsersTable


class PublicationEdit(BaseModel):
    Template_UUID: Optional[uuid.UUID] = None
    Title: Optional[str] = None


@inject
def post_edit_publication_endpoint(
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_edit_publication,
            )
        ),
    ],
    publication: Annotated[PublicationTable, Depends(depends_publication)],
    template_repository: Annotated[
        PublicationTemplateRepository, Depends(Provide[ApiContainer.publication.template_repository])
    ],
    session: Annotated[Session, Depends(depends_db_session)],
    object_in: PublicationEdit,
) -> ResponseOK:
    if not publication.Module.is_active:
        raise HTTPException(status.HTTP_409_CONFLICT, "This module is not active")

    changes: Dict[str, Any] = object_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    if object_in.Template_UUID is not None:
        _guard_template(session, template_repository, publication.Document_Type, object_in.Template_UUID)

    for key, value in changes.items():
        setattr(publication, key, value)

    publication.Modified_By_UUID = user.UUID
    publication.Modified_Date = datetime.now(timezone.utc)

    session.add(publication)
    session.commit()
    session.flush()

    return ResponseOK(message="OK")


def _guard_template(
    session: Session,
    template_repository: PublicationTemplateRepository,
    document_type: str,
    template_uuid: uuid.UUID,
) -> None:
    template: Optional[PublicationTemplateTable] = template_repository.get_by_uuid(session, template_uuid)
    if template is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template niet gevonden")
    if not template.Is_Active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template is gesloten")
    if template.Document_Type != document_type:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template hoort niet bij dit document type")
