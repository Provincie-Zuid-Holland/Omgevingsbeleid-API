import uuid
from datetime import UTC, datetime
from typing import Annotated

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
    title: str = Field(..., min_length=3)
    description: str
    document_type: DocumentType
    object_types: list[str]
    object_field_map: dict[str, list[str]]
    text_template: str
    object_templates: dict[str, str]


class TemplateCreatedResponse(BaseModel):
    id: uuid.UUID


def post_create_template_endpoint(
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_create_publication_template,
            )
        ),
    ],
    session: Annotated[Session, Depends(depends_db_session)],
    object_in: TemplateCreate,
) -> TemplateCreatedResponse:
    timepoint: datetime = datetime.now(UTC)

    template = PublicationTemplateTable(
        id=uuid.uuid4(),
        title=object_in.title,
        description=object_in.description,
        is_active=True,
        document_type=object_in.document_type,
        object_types=object_in.object_types,
        object_field_map=object_in.object_field_map,
        text_template=object_in.text_template,
        object_templates=object_in.object_templates,
        created_date=timepoint,
        modified_date=timepoint,
        created_by_id=user.UUID,
        modified_by_id=user.UUID,
    )

    session.add(template)
    session.flush()
    session.commit()

    return TemplateCreatedResponse(
        id=template.id,
    )
