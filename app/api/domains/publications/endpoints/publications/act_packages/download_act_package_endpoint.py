from datetime import datetime, timezone
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Response
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.publications.dependencies import depends_publication_zip_by_act_package
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationPackageZipTable
from app.core.tables.users import UsersTable


@inject
async def get_download_act_package_endpoint(
    package_zip: Annotated[PublicationPackageZipTable, Depends(depends_publication_zip_by_act_package)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_download_publication_act_package,
            )
        ),
    ],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
) -> Response:
    package_zip.Latest_Download_Date = datetime.now(timezone.utc)
    package_zip.Latest_Download_By_UUID = user.UUID

    db.add(package_zip)
    db.commit()
    db.flush()

    return Response(
        content=package_zip.Binary,
        media_type="application/x-zip-compressed",
        headers={
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Content-Disposition": f"attachment; filename={package_zip.Filename}",
        },
    )
