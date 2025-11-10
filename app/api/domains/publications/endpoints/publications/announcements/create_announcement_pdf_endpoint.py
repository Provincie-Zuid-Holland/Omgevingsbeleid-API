from typing import Annotated

import requests
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.publications.dependencies import depends_publication_announcement
from app.api.domains.publications.exceptions import DSOConfigurationException
from app.api.domains.publications.services.announcement_package.announcement_package_builder import (
    AnnouncementPackageBuilder,
)
from app.api.domains.publications.services.announcement_package.announcement_package_builder_factory import (
    AnnouncementPackageBuilderFactory,
)
from app.api.domains.publications.services.pdf_export_service import PdfExportError, PdfExportService
from app.api.domains.publications.types.enums import PackageType
from app.api.domains.publications.types.zip import ZipData
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.exceptions import LoggedHttpException
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationAnnouncementTable
from app.core.tables.users import UsersTable


@inject
def post_create_announcement_pdf_endpoint(
    announcement: Annotated[PublicationAnnouncementTable, Depends(depends_publication_announcement)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_create_publication_announcement_package,
            )
        ),
    ],
    session: Annotated[Session, Depends(depends_db_session)],
    package_builder_factory: Annotated[
        AnnouncementPackageBuilderFactory,
        Depends(
            Provide[ApiContainer.publication.announcement_package_builder_factory],
        ),
    ],
    pdf_export_service: Annotated[PdfExportService, Depends(Provide[ApiContainer.publication.pdf_export_service])],
) -> StreamingResponse:
    if not announcement.Publication.Module.is_active:
        raise HTTPException(status.HTTP_409_CONFLICT, "This module is not active")

    try:
        package_builder: AnnouncementPackageBuilder = package_builder_factory.create_builder(
            session,
            announcement,
            PackageType.VALIDATION,
        )
        package_builder.build_publication_files()
        zip_data: ZipData = package_builder.zip_files()

        pdf_response: requests.Response = pdf_export_service.create_pdf(
            announcement.Publication.Environment.Code or "",
            zip_data,
        )

        filename: str = f"{zip_data.Filename.removesuffix('.zip')}.pdf"
        response = StreamingResponse(
            pdf_response.iter_content(chunk_size=1024),
            media_type="application/pdf",
            headers={
                "Access-Control-Expose-Headers": "Content-Disposition",
                "Content-Disposition": f"attachment; filename={filename}",
            },
        )

        return response

    except HTTPException as e:
        # This is already correctly formatted
        raise e
    except ValidationError as e:
        raise HTTPException(441, e.errors())
    except DSOConfigurationException as e:
        raise LoggedHttpException(status_code=442, detail=e.message)
    except PdfExportError as e:
        raise LoggedHttpException(status_code=444, detail=e.msg)
    except Exception as e:
        # We do not know what to except here
        # This will result in a 500 server error
        raise e
