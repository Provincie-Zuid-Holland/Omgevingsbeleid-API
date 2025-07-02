from datetime import datetime, timezone
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.publications.dependencies import depends_publication_act_active
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.types import ResponseOK
from app.core.tables.publications import PublicationActTable
from app.core.tables.users import UsersTable


@inject
async def post_close_act_endpoint(
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_close_publication_act,
            )
        ),
    ],
    act: Annotated[PublicationActTable, Depends(depends_publication_act_active)],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
) -> ResponseOK:
    act.Modified_By_UUID = user.UUID
    act.Modified_Date = datetime.now(timezone.utc)
    act.Is_Active = False

    db.add(act)
    db.commit()
    db.flush()

    return ResponseOK()
