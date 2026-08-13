from typing import Annotated
from fastapi import Depends, HTTPException, status, Response

from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationVersionAttachmentTable, PublicationVersionTable
from app.api.domains.publications.dependencies import (
    depends_publication_version,
    depends_publication_version_attachment,
)
from app.core.tables.users import UsersTable


def get_download_attachment_endpoint(
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
) -> Response:
    _guard(version, attachment)
    filename = attachment.File.Filename
    content = attachment.File.Binary
    content_type = attachment.File.Content_Type

    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Length": str(len(content)),
        },
    )


def _guard(version: PublicationVersionTable, attachment: PublicationVersionAttachmentTable) -> None:
    if attachment.Publication_Version_UUID != version.UUID:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "You can not download an attachment of another publication version"
        )
    if not version.Publication.Act.Is_Active:
        raise HTTPException(status.HTTP_409_CONFLICT, "This act can no longer be used")
