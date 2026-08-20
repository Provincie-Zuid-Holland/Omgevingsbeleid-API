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
from app.api.services import PermissionService
from app.core.tables.others import HoofdlijnTable
from app.core.tables.users import UsersTable


class CreateHoofdlijn(BaseModel):
    Name: str | None = Field(None)
    Type: str | None = Field(None)

    model_config = ConfigDict(from_attributes=True)

class HoofdlijnCreatedResponse(BaseModel):
    UUID: uuid.UUID


@inject
def post_hoofdlijnen_create_endpoint(
    logged_in_user: Annotated[UsersTable, Depends(depends_current_user)],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    session: Annotated[Session, Depends(depends_db_session)],
    object_in: CreateHoofdlijn,
) -> HoofdlijnCreatedResponse:
    permission_service.guard_valid_user(Permissions.can_create_hoofdlijn, logged_in_user)

    timepoint: datetime = datetime.now(UTC)

    hoofdlijn: HoofdlijnTable = HoofdlijnTable(
        UUID=uuid.uuid4(),
        Name=object_in.Name,
        Type=object_in.Type,
        Created_Date=timepoint,
        Created_By_UUID=logged_in_user.UUID,
        Modified_Date=timepoint,
        Modified_By_UUID=logged_in_user.UUID,
    )

    session.add(hoofdlijn)
    session.flush()
    session.commit()

    return HoofdlijnCreatedResponse(
        UUID=hoofdlijn.UUID,
    )
