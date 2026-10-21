from typing import Annotated

from fastapi import Depends, HTTPException, Response, status

from app.api.domains.publications.dependencies import (
    depends_publication_version,
    depends_publication_version_attachment,
)
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationVersionAttachmentTable, PublicationVersionTable
from app.core.tables.users import UsersTable


def get_download_attachment_endpoint(
    version: Annotated[PublicationVersionTable, Depends(depends_publication_version)],
    attachment: Annotated[PublicationVersionAttachmentTable, Depends(depends_publication_version_attachment)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_download_publication_version_attachment,
            )
        ),
    ],
) -> Response:
    _guard(version, attachment)
    filename = attachment.file.filename
    content = attachment.file.binary
    content_type = attachment.file.content_type

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
    if attachment.publication_version_id != version.id:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "You can not download an attachment of another publication version"
        )
    if not version.publication.act.is_active:
        raise HTTPException(status.HTTP_409_CONFLICT, "This act can no longer be used")
