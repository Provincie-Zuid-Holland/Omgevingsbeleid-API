import json
from datetime import UTC, datetime
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
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


@inject
def delete_hoofdlijnen_endpoint(
    logged_in_user: Annotated[UsersTable, Depends(depends_current_user)],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    session: Annotated[Session, Depends(depends_db_session)],
    hoofdlijn: Annotated[HoofdlijnTable, Depends(depends_hoofdlijn)],
) -> ResponseOK:
    permission_service.guard_valid_user(Permissions.hoofdlijnen_can_delete_hoofdlijn, logged_in_user)

    change_log = ChangeLogTable(
        Created_Date=datetime.now(UTC),
        Created_By_UUID=logged_in_user.UUID,
        Action_Type="delete_hoofdlijn",
        Action_Data=json.dumps(hoofdlijn.to_dict()),
    )

    session.add(change_log)
    session.delete(hoofdlijn)
    session.flush()
    session.commit()

    return ResponseOK(message="OK")
