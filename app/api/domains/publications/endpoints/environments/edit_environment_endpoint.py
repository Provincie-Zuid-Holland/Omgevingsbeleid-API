from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import depends_db_session
from app.api.domains.publications.dependencies import depends_publication_environment
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.types import ResponseOK
from app.core.tables.publications import PublicationEnvironmentTable
from app.core.tables.users import UsersTable


class EnvironmentEdit(BaseModel):
    title: str | None = None
    description: str | None = None

    province_id: str | None = None
    authority_id: str | None = None
    submitter_id: str | None = None

    frbr_country: str | None = None
    frbr_language: str | None = None

    is_active: bool | None = None
    can_validate: bool | None = None
    can_publicate: bool | None = None


def post_edit_environment_endpoint(
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_edit_publication_environment,
            )
        ),
    ],
    environment: Annotated[PublicationEnvironmentTable, Depends(depends_publication_environment)],
    session: Annotated[Session, Depends(depends_db_session)],
    object_in: EnvironmentEdit,
) -> ResponseOK:
    changes: dict[str, Any] = object_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    for key, value in changes.items():
        setattr(environment, key, value)

    environment.modified_by_id = user.UUID
    environment.modified_date = datetime.now(UTC)

    session.add(environment)
    session.flush()
    session.commit()

    return ResponseOK(message="OK")
