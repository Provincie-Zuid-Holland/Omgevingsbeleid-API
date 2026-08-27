import json
from datetime import UTC, datetime
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.others.dependencies import depends_hoofdlijn
from app.api.domains.users.dependencies import depends_current_user
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.api.types import ResponseOK
from app.core.tables.others import ChangeLogTable, HoofdlijnTable
from app.core.tables.users import UsersTable


class EditHoofdlijn(BaseModel):
    Name: str | None = Field(default=None, min_length=3, max_length=255)
    Type: str | None = Field(default=None, min_length=3, max_length=255)

    model_config = ConfigDict(from_attributes=True)


@inject
def post_hoofdlijnen_edit_endpoint(
    logged_in_user: Annotated[UsersTable, Depends(depends_current_user)],
    hoofdlijn: Annotated[HoofdlijnTable, Depends(depends_hoofdlijn)],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    session: Annotated[Session, Depends(depends_db_session)],
    object_in: EditHoofdlijn,
) -> ResponseOK:
    permission_service.guard_valid_user(Permissions.can_edit_hoofdlijn, logged_in_user)

    hoofdlijn_before = hoofdlijn.to_dict()

    changes: dict = object_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    timepoint: datetime = datetime.now(UTC)

    for key, value in changes.items():
        setattr(hoofdlijn, key, value)

    hoofdlijn.Modified_By_UUID = logged_in_user.UUID
    hoofdlijn.Modified_Date = timepoint

    hoofdlijn_after = hoofdlijn.to_dict()

    change_log = ChangeLogTable(
        Created_Date=datetime.now(UTC),
        Created_By_UUID=logged_in_user.UUID,
        Action_Type="edit_hoofdlijn",
        Action_Data=json.dumps(changes),
        Before=json.dumps(hoofdlijn_before),
        After=json.dumps(hoofdlijn_after),
    )

    session.add(change_log)
    session.add(hoofdlijn)
    session.flush()
    session.commit()

    return ResponseOK(message="OK")
