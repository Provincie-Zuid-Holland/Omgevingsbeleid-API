from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import depends_db_session
from app.api.domains.publications.dependencies import (
    depends_publication_version,
    depends_publication_version_attachment,
)
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.types import ResponseOK
from app.core.tables.publications import PublicationVersionAttachmentTable, PublicationVersionTable
from app.core.tables.users import UsersTable


def post_delete_attachment_endpoint(
    version: Annotated[PublicationVersionTable, Depends(depends_publication_version)],
    attachment: Annotated[PublicationVersionAttachmentTable, Depends(depends_publication_version_attachment)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_edit_publication_version,
            )
        ),
    ],
    session: Annotated[Session, Depends(depends_db_session)],
) -> ResponseOK:
    return ResponseOK(message="OK")
    # _guard(version, attachment)

    # # @todo: This should become a soft delete but I could not upgrade the database at this point
    # db.delete(attachment.File)
    # db.delete(attachment)
    # db.commit()
    # db.flush()

    # return ResponseOK(message="OK")


def _guard(version: PublicationVersionTable, attachment: PublicationVersionAttachmentTable) -> None:
    if attachment.Publication_Version_UUID != version.UUID:
        raise HTTPException(status.HTTP_409_CONFLICT, "You can not delete an attachment of another publication version")
    if not version.Publication.Act.Is_Active:
        raise HTTPException(status.HTTP_409_CONFLICT, "This act can no longer be used")
    if version.Is_Locked:
        raise HTTPException(status.HTTP_409_CONFLICT, "This publication version is locked")
