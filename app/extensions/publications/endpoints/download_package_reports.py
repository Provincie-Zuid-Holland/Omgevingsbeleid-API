import uuid

from fastapi import APIRouter, Depends, HTTPException, Response

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_publication_repository
from app.extensions.publications.repository import PublicationRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class DownloadPackageReportsEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            package_uuid: uuid.UUID,
            pub_repository: PublicationRepository = Depends(depends_publication_repository),
            user: UsersTable = Depends(depends_current_active_user),
        ):
            # retrieve all reports for a package
            package = pub_repository.get_publication_package(uuid=package_uuid)
            if not package:
                raise HTTPException(status_code=404, detail="Package not found")
            if package.Validation_Status == "Pending":
                raise HTTPException(status_code=404, detail="Package reports are not available yet")

            # For every report in package.Reports, concatenate the report.Source_Document into a response file xml
            response_xml = ""
            for report in package.Reports:
                response_xml += report.Source_Document
                # separate files with new line
                response_xml += "\n"

            filename = f"package_{package.UUID.hex}_reports.xml"

            return Response(
                content=response_xml,
                media_type="application/xml",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            summary=f"Download package reports",
            description=None,
            tags=["Publications"],
        )

        return router


class DownloadPackageReportsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "download_publication_package_reports"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{package_uuid}" in path:
            raise RuntimeError("Missing {package_uuid} argument in path")

        return DownloadPackageReportsEndpoint(path=path)
