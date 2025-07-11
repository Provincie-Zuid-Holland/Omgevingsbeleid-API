from datetime import datetime, timezone
from typing import Annotated

from dependency_injector.wiring import inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies import depends_db_session
from app.api.domains.publications.dependencies import depends_publication_act_active
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.types import ResponseOK
from app.core.tables.publications import PublicationActTable
from app.core.tables.users import UsersTable


@inject
def post_close_act_endpoint(
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_close_publication_act,
            )
        ),
    ],
    act: Annotated[PublicationActTable, Depends(depends_publication_act_active)],
    session: Annotated[Session, Depends(depends_db_session)],
) -> ResponseOK:
    act.Modified_By_UUID = user.UUID
    act.Modified_Date = datetime.now(timezone.utc)
    act.Is_Active = False

    session.add(act)
    session.commit()
    session.flush()

    return ResponseOK(message="OK")
