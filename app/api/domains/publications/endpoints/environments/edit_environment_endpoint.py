from datetime import datetime, timezone
from typing import Annotated, Any, Dict, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
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


@inject
async def post_edit_environment_endpoint(
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
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
) -> ResponseOK:
    changes: Dict[str, Any] = object_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    for key, value in changes.items():
        setattr(environment, key, value)

    environment.Modified_By_UUID = user.UUID
    environment.Modified_Date = datetime.now(timezone.utc)

    db.add(environment)
    db.flush()
    db.commit()

    return ResponseOK()
