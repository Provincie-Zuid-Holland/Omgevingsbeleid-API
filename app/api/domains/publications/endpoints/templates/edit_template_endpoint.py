from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import depends_db_session
from app.api.domains.publications.dependencies import depends_publication_template
from app.api.domains.publications.types.enums import DocumentType
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.types import ResponseOK
from app.core.tables.publications import PublicationTemplateTable
from app.core.tables.users import UsersTable


class TemplateEdit(BaseModel):
    Title: str | None = None
    Description: str | None = None
    Is_Active: bool | None = None
    Document_Type: DocumentType | None = None
    Field_Map: list[str] | None = Field(None, deprecated=True)
    Object_Field_Map: dict[str, list[str]] | None = None
    Object_Types: list[str] | None = None
    Text_Template: str | None = None
    Object_Templates: dict[str, str] | None = None


def post_edit_template_endpoint(
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_edit_publication_template,
            )
        ),
    ],
    template: Annotated[PublicationTemplateTable, Depends(depends_publication_template)],
    session: Annotated[Session, Depends(depends_db_session)],
    object_in: TemplateEdit,
) -> ResponseOK:
    changes: dict[str, Any] = object_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    for key, value in changes.items():
        setattr(template, key, value)

    template.Modified_By_UUID = user.UUID
    template.Modified_Date = datetime.now(UTC)

    session.add(template)
    session.flush()
    session.commit()

    return ResponseOK(message="OK")
