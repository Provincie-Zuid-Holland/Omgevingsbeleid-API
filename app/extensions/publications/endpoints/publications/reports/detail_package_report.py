from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_publication_report
from app.extensions.publications.models import PublicationPackageReport
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.tables.tables import PublicationPackageReportTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class DetailPackageReportEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            report: PublicationPackageReportTable = Depends(depends_publication_report),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_view_publication_package_report,
                )
            ),
        ) -> PublicationPackageReport:
            result: PublicationPackageReport = PublicationPackageReport.from_orm(report)
            return result

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PublicationPackageReport,
            summary=f"Get details of a publication report",
            description=None,
            tags=["Publication Reports"],
        )

        return router


class DetailPackageReportEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "detail_publication_package_report"

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

        if not "{report_uuid}" in path:
            raise RuntimeError("Missing {report_uuid} argument in path")

        return DetailPackageReportEndpoint(path=path)
