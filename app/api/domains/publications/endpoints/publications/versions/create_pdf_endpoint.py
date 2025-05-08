from typing import Annotated, List

import requests
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError

from app.api.api_container import ApiContainer
from app.api.domains.publications.dependencies import depends_publication_version
from app.api.domains.publications.exceptions import DSOConfigurationException, DSORenvooiException
from app.api.domains.publications.services.act_package.act_package_builder import ActPackageBuilder
from app.api.domains.publications.services.act_package.act_package_builder_factory import ActPackageBuilderFactory
from app.api.domains.publications.services.pdf_export_service import PdfExportError, PdfExportService
from app.api.domains.publications.services.publication_version_validator import PublicationVersionValidator
from app.api.domains.publications.types.enums import MutationStrategy, PackageType
from app.api.domains.publications.types.zip import ZipData
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.exceptions import LoggedHttpException
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationVersionTable
from app.core.tables.users import UsersTable


class PublicationPackagePdf(BaseModel):
    Mutation: MutationStrategy = Field(MutationStrategy.RENVOOI)


@inject
def post_create_pdf_endpoint(
    object_in: Annotated[PublicationPackagePdf, Depends()],
    version: Annotated[PublicationVersionTable, Depends(depends_publication_version)],
    validator: Annotated[PublicationVersionValidator, Depends(Provide[ApiContainer.publication.version_validator])],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_create_publication_act_package,
            )
        ),
    ],
    package_builder_factory: Annotated[
        ActPackageBuilderFactory, Depends(Provide[ApiContainer.publication.act_package_builder_factory])
    ],
    pdf_export_service: Annotated[PdfExportService, Depends(Provide[ApiContainer.publication.pdf_export_service])],
) -> StreamingResponse:
    _guard_valid_publication_version(validator, version)

    try:
        package_builder: ActPackageBuilder = package_builder_factory.create_builder(
            version,
            PackageType.VALIDATION,
            object_in.Mutation,
        )
        package_builder.build_publication_files()
        zip_data: ZipData = package_builder.zip_files()

        pdf_response: requests.Response = pdf_export_service.create_pdf(
            version.Publication.Environment.Code or "",
            zip_data,
        )

        filename: str = f"{zip_data.Filename.removesuffix('.zip')}-{object_in.Mutation.value}.pdf"
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
    except DSORenvooiException as e:
        raise LoggedHttpException(status_code=443, detail=e.message, log_message=e.internal_error)
    except PdfExportError as e:
        raise LoggedHttpException(status_code=444, detail=e.msg)
    except Exception as e:
        # We do not know what to except here
        # This will result in a 500 server error
        raise e


def _guard_valid_publication_version(
    validator: PublicationVersionValidator,
    version: PublicationVersionTable,
) -> None:
    errors: List[dict] = validator.get_errors(version)
    if len(errors) != 0:
        raise HTTPException(status.HTTP_409_CONFLICT, errors)
