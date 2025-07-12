from datetime import datetime, timezone
from typing import Annotated, Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import depends_db_session
from app.api.domains.publications.dependencies import depends_publication_environment
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.types import ResponseOK
from app.core.tables.publications import PublicationEnvironmentTable
from app.core.tables.users import UsersTable


class EnvironmentEdit(BaseModel):
    Title: Optional[str] = Field(None)
    Description: Optional[str] = Field(None)

    Province_ID: Optional[str] = Field(None)
    Authority_ID: Optional[str] = Field(None)
    Submitter_ID: Optional[str] = Field(None)

    Frbr_Country: Optional[str] = Field(None)
    Frbr_Language: Optional[str] = Field(None)

    Is_Active: Optional[bool] = Field(None)
    Can_Validate: Optional[bool] = Field(None)
    Can_Publicate: Optional[bool] = Field(None)


def post_edit_environment_endpoint(
    object_in: Annotated[EnvironmentEdit, Depends()],
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
) -> ResponseOK:
    changes: Dict[str, Any] = object_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    for key, value in changes.items():
        setattr(environment, key, value)

    environment.Modified_By_UUID = user.UUID
    environment.Modified_Date = datetime.now(timezone.utc)

    session.add(environment)
    session.flush()
    session.commit()

    return ResponseOK(message="OK")
