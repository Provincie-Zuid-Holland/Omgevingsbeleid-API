from datetime import datetime, timezone
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.publications.dependencies import depends_publication_version
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.types import ResponseOK
from app.core.tables.publications import PublicationVersionTable
from app.core.tables.users import UsersTable


@inject
async def post_delete_version_endpoint(
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_edit_publication_version,
            )
        ),
    ],
    version: Annotated[PublicationVersionTable, Depends(depends_publication_version)],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
) -> ResponseOK:
    if version.Deleted_At is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Publication Version already deleted")

    if version.Act_Packages:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Publication Version has related Act Packages, cannot delete")

    timepoint: datetime = datetime.now(timezone.utc)
    version.Deleted_At = timepoint
    version.Modified_By_UUID = user.UUID
    version.Modified_Date = timepoint

    db.add(version)
    db.commit()
    db.flush()

    return ResponseOK()
