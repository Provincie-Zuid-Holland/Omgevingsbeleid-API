import uuid
from datetime import datetime, timezone
from typing import Annotated, Dict, List

from dependency_injector.wiring import inject
from fastapi import Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import depends_db_session
from app.api.domains.publications.types.enums import DocumentType
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationTemplateTable
from app.core.tables.users import UsersTable


class TemplateCreate(BaseModel):
    Title: str = Field(..., min_length=3)
    Description: str
    Document_Type: DocumentType
    Object_Types: List[str]
    Field_Map: List[str]
    Text_Template: str
    Object_Templates: Dict[str, str]


class TemplateCreatedResponse(BaseModel):
    UUID: uuid.UUID


@inject
def post_create_template_endpoint(
    object_in: Annotated[TemplateCreate, Depends()],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_create_publication_template,
            )
        ),
    ],
    session: Annotated[Session, Depends(depends_db_session)],
) -> TemplateCreatedResponse:
    timepoint: datetime = datetime.now(timezone.utc)

    template = PublicationTemplateTable(
        UUID=uuid.uuid4(),
        Title=object_in.Title,
        Description=object_in.Description,
        Is_Active=True,
        Document_Type=object_in.Document_Type,
        Object_Types=object_in.Object_Types,
        Field_Map=object_in.Field_Map,
        Text_Template=object_in.Text_Template,
        Object_Templates=object_in.Object_Templates,
        Created_Date=timepoint,
        Modified_Date=timepoint,
        Created_By_UUID=user.UUID,
        Modified_By_UUID=user.UUID,
    )

    session.add(template)
    session.flush()
    session.commit()

    return TemplateCreatedResponse(
        UUID=template.UUID,
    )
