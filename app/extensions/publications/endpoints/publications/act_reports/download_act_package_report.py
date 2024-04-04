from fastapi import APIRouter, Depends, Response
from lxml import etree

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_publication_act_report
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.tables.tables import PublicationActPackageReportTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class DownloadActPackageReportEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            report: PublicationActPackageReportTable = Depends(depends_publication_act_report),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_download_publication_act_package_report,
                )
            ),
        ) -> Response:
            return self._handler(report)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            summary=f"Download publication package report",
            description=None,
            tags=["Publication Act Reports"],
        )

        return router

    def _handler(self, report: PublicationActPackageReportTable) -> Response:
        content = report.Source_Document

        try:
            xml_tree = etree.fromstring(content)
            content = etree.tostring(xml_tree, pretty_print=True).decode()
        except:
            pass

        response = Response(
            content=report.Source_Document,
            media_type="application/xml",
            headers={
                "Access-Control-Expose-Headers": "Content-Disposition",
                "Content-Disposition": f"attachment; filename={report.Filename}",
            },
        )
        return response


class DownloadActPackageReportEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "download_publication_act_package_report"

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
        if not "{act_report_uuid}" in path:
            raise RuntimeError("Missing {act_report_uuid} argument in path")

        return DownloadActPackageReportEndpoint(path=path)
