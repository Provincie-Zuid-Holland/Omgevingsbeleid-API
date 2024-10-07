from typing import List

import requests
from dso.exceptions import RenvooiError
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import (
    depends_act_package_builder_factory,
    depends_pdf_export_service,
    depends_publication_version,
    depends_publication_version_validator,
)
from app.extensions.publications.enums import MutationStrategy, PackageType
from app.extensions.publications.exceptions import DSOConfigurationException
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.services.act_package.act_package_builder import ActPackageBuilder, ZipData
from app.extensions.publications.services.act_package.act_package_builder_factory import ActPackageBuilderFactory
from app.extensions.publications.services.pdf_export_service import PdfExportError, PdfExportService
from app.extensions.publications.services.publication_version_validator import PublicationVersionValidator
from app.extensions.publications.tables.tables import (
    PublicationActTable,
    PublicationEnvironmentTable,
    PublicationTable,
    PublicationVersionTable,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class PublicationPackagePdf(BaseModel):
    Mutation: MutationStrategy = Field(MutationStrategy.RENVOOI)


class EndpointHandler:
    def __init__(
        self,
        pdf_export_service: PdfExportService,
        validator: PublicationVersionValidator,
        package_builder_factory: ActPackageBuilderFactory,
        object_in: PublicationPackagePdf,
        publication_version: PublicationVersionTable,
    ):
        self._pdf_export_service: PdfExportService = pdf_export_service
        self._validator: PublicationVersionValidator = validator
        self._package_builder_factory: ActPackageBuilderFactory = package_builder_factory
        self._object_in: PublicationPackagePdf = object_in
        self._publication_version: PublicationVersionTable = publication_version
        self._publication: PublicationTable = publication_version.Publication
        self._environment: PublicationEnvironmentTable = publication_version.Publication.Environment
        self._act: PublicationActTable = publication_version.Publication.Act

    def handle(self) -> StreamingResponse:
        self._guard_valid_publication_version()

        try:
            package_builder: ActPackageBuilder = self._package_builder_factory.create_builder(
                self._publication_version,
                PackageType.VALIDATION,
                self._object_in.Mutation,
            )
            package_builder.build_publication_files()
            zip_data: ZipData = package_builder.zip_files()

            pdf_response: requests.Response = self._pdf_export_service.create_pdf(
                self._environment.Code,
                zip_data,
            )

            filename: str = f"{zip_data.Filename.removesuffix('.zip')}-{self._object_in.Mutation.value}.pdf"
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
            raise HTTPException(status_code=441, detail=e.errors())
        except DSOConfigurationException as e:
            raise HTTPException(status_code=442, detail=e.message)
        except RenvooiError as e:
            raise HTTPException(status_code=443, detail=e.msg)
        except PdfExportError as e:
            raise HTTPException(status_code=444, detail=e.msg)
        except Exception as e:
            # We do not know what to except here
            # This will result in a 500 server error
            raise e

    def _guard_valid_publication_version(self):
        errors: List[dict] = self._validator.get_errors(self._publication_version)
        if len(errors) != 0:
            raise HTTPException(status_code=409, detail=errors)


class CreatePublicationVersionPdfEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: PublicationPackagePdf,
            publication_version: PublicationVersionTable = Depends(depends_publication_version),
            publication_version_validator: PublicationVersionValidator = Depends(depends_publication_version_validator),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_create_publication_act_package,
                )
            ),
            package_builder_factory: ActPackageBuilderFactory = Depends(depends_act_package_builder_factory),
            pdf_export_service: PdfExportService = Depends(depends_pdf_export_service),
        ) -> StreamingResponse:
            handler: EndpointHandler = EndpointHandler(
                pdf_export_service,
                publication_version_validator,
                package_builder_factory,
                object_in,
                publication_version,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=None,
            summary="Download Publication Version as Pdf",
            tags=["Publication Versions"],
        )

        return router


class CreatePublicationVersionPdfEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "create_publication_version_pdf"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        if not "{version_uuid}" in path:
            raise RuntimeError("Missing {version_uuid} argument in path")

        return CreatePublicationVersionPdfEndpoint(path=path)
