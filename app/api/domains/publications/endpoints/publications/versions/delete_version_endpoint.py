from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import depends_db_session
from app.api.domains.publications.dependencies import depends_publication_version
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.types import ResponseOK
from app.core.tables.publications import PublicationVersionTable
from app.core.tables.users import UsersTable


def post_delete_version_endpoint(
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_edit_publication_version,
            )
        ),
    ],
    version: Annotated[PublicationVersionTable, Depends(depends_publication_version)],
    session: Annotated[Session, Depends(depends_db_session)],
) -> ResponseOK:
    if not version.publication.module.is_active:
        raise HTTPException(status.HTTP_409_CONFLICT, "This module is not active")
    if version.deleted_at is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Publication Version already deleted")
    if version.act_packages:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Publication Version has related Act Packages, cannot delete")

    timepoint: datetime = datetime.now(UTC)
    version.deleted_at = timepoint
    version.modified_by_id = user.UUID
    version.modified_date = timepoint

    session.add(version)
    session.flush()
    session.commit()

    return ResponseOK(message="OK")
