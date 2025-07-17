from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, Response
from sqlalchemy.orm import Session

from app.api.dependencies import depends_db_session
from app.api.domains.publications.dependencies import depends_publication_zip_by_act_package
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationPackageZipTable
from app.core.tables.users import UsersTable


def get_download_act_package_endpoint(
    package_zip: Annotated[PublicationPackageZipTable, Depends(depends_publication_zip_by_act_package)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_download_publication_act_package,
            )
        ),
    ],
    session: Annotated[Session, Depends(depends_db_session)],
) -> Response:
    package_zip.Latest_Download_Date = datetime.now(timezone.utc)
    package_zip.Latest_Download_By_UUID = user.UUID

    filename = package_zip.Filename
    content = package_zip.Binary

    session.add(package_zip)
    session.commit()

    return Response(
        content=content,
        media_type="application/x-zip-compressed",
        headers={
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Content-Disposition": f"attachment; filename={filename}",
        },
    )
