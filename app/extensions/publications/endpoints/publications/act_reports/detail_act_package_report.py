from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_publication_act_report
from app.extensions.publications.models import PublicationActPackageReport
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.tables.tables import PublicationActPackageReportTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class DetailActPackageReportEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            report: PublicationActPackageReportTable = Depends(depends_publication_act_report),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_view_publication_act_package_report,
                )
            ),
        ) -> PublicationActPackageReport:
            result: PublicationActPackageReport = PublicationActPackageReport.model_validate(report)
            return result

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PublicationActPackageReport,
            summary=f"Get details of a publication report",
            description=None,
            tags=["Publication Act Reports"],
        )

        return router


class DetailActPackageReportEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "detail_publication_act_package_report"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        if not "{act_report_uuid}" in path:
            raise RuntimeError("Missing {act_report_uuid} argument in path")

        return DetailActPackageReportEndpoint(path=path)
