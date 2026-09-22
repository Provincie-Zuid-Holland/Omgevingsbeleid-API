import json
import uuid
from datetime import UTC, datetime
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.users.dependencies import depends_current_user
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.core.tables.others import ChangeLogTable, HoofdlijnTable
from app.core.tables.users import UsersTable


class CreateHoofdlijn(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    type: str = Field(..., min_length=3, max_length=255)

    model_config = ConfigDict(from_attributes=True)


class HoofdlijnCreatedResponse(BaseModel):
    id: uuid.UUID


@inject
def post_hoofdlijnen_create_endpoint(
    logged_in_user: Annotated[UsersTable, Depends(depends_current_user)],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    session: Annotated[Session, Depends(depends_db_session)],
    object_in: CreateHoofdlijn,
) -> HoofdlijnCreatedResponse:
    permission_service.guard_valid_user(Permissions.hoofdlijnen_can_create_hoofdlijn, logged_in_user)

    timepoint: datetime = datetime.now(UTC)

    hoofdlijn: HoofdlijnTable = HoofdlijnTable(
        id=uuid.uuid4(),
        name=object_in.name,
        type=object_in.type,
        Created_Date=timepoint,
        Created_By_UUID=logged_in_user.UUID,
        Modified_Date=timepoint,
        Modified_By_UUID=logged_in_user.UUID,
    )

    change_log: ChangeLogTable = ChangeLogTable(
        created_date=datetime.now(UTC),
        created_by=logged_in_user.UUID,
        action_type="create_hoofdlijn",
        action_data=json.dumps(hoofdlijn.to_dict()),
    )

    session.add(hoofdlijn)
    session.add(change_log)
    session.flush()
    session.commit()

    return HoofdlijnCreatedResponse(
        id=hoofdlijn.id,
    )
