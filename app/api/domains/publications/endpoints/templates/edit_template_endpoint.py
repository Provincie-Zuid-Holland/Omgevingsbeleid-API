from datetime import datetime, timezone
from typing import Annotated, Any, Dict, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.publications.dependencies import depends_publication_template
from app.api.domains.publications.types.enums import DocumentType
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.types import ResponseOK
from app.core.tables.publications import PublicationTemplateTable
from app.core.tables.users import UsersTable


class TemplateEdit(BaseModel):
    Title: Optional[str] = None
    Description: Optional[str] = None
    Is_Active: Optional[bool] = None
    Document_Type: Optional[DocumentType] = None
    Field_Map: Optional[List[str]] = None
    Object_Types: Optional[List[str]] = None
    Text_Template: Optional[str] = None
    Object_Templates: Optional[Dict[str, str]] = None


@inject
def post_edit_template_endpoint(
    object_in: Annotated[TemplateEdit, Depends()],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_edit_publication_template,
            )
        ),
    ],
    template: Annotated[PublicationTemplateTable, Depends(depends_publication_template)],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
) -> ResponseOK:
    changes: Dict[str, Any] = object_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    for key, value in changes.items():
        setattr(template, key, value)

    template.Modified_By_UUID = user.UUID
    template.Modified_Date = datetime.now(timezone.utc)

    db.add(template)
    db.commit()
    db.flush()

    return ResponseOK()
