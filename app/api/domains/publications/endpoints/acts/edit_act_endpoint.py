from datetime import datetime, timezone
from typing import Annotated, Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import depends_db_session
from app.api.domains.publications.dependencies import depends_publication_act_active
from app.api.domains.publications.types.models import ActMetadata
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.types import ResponseOK
from app.core.tables.publications import PublicationActTable
from app.core.tables.users import UsersTable


class ActEdit(BaseModel):
    Title: Optional[str] = Field(None)
    Metadata: Optional[ActMetadata] = None


def post_edit_act_endpoint(
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_edit_publication_act,
            )
        ),
    ],
    act: Annotated[PublicationActTable, Depends(depends_publication_act_active)],
    session: Annotated[Session, Depends(depends_db_session)],
    object_in: ActEdit,
) -> ResponseOK:
    changes: Dict[str, Any] = object_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    for key, value in changes.items():
        if isinstance(value, BaseModel):
            value = value.model_dump()
        setattr(act, key, value)

    act.Modified_By_UUID = user.UUID
    act.Modified_Date = datetime.now(timezone.utc)

    session.add(act)
    session.commit()
    session.flush()

    return ResponseOK(message="OK")
