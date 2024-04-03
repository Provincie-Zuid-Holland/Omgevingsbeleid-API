import uuid
from typing import Optional

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_simple_pagination
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PagedResponse, SimplePagination
from app.extensions.publications.dependencies import depends_publication_act_report_repository
from app.extensions.publications.enums import ReportStatusType
from app.extensions.publications.models import PublicationActPackageReportShort
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.repository.publication_act_report_repository import PublicationActReportRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class ListActPackageReportsEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            act_package_uuid: Optional[uuid.UUID] = None,
            report_status: Optional[ReportStatusType] = None,
            pagination: SimplePagination = Depends(depends_simple_pagination),
            report_repository: PublicationActReportRepository = Depends(depends_publication_act_report_repository),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_view_publication_act_package_report,
                )
            ),
        ) -> PagedResponse[PublicationActPackageReportShort]:
            return self._handler(
                report_repository,
                act_package_uuid,
                report_status,
                pagination,
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[PublicationActPackageReportShort],
            summary="List the existing Publication Act reports",
            description=None,
            tags=["Publication Act Reports"],
        )

        return router

    def _handler(
        self,
        report_repository: PublicationActReportRepository,
        package_uuid: Optional[uuid.UUID],
        report_status: Optional[ReportStatusType],
        pagination: SimplePagination,
    ):
        paginated_result = report_repository.get_with_filters(
            package_uuid=package_uuid,
            report_status=report_status,
            offset=pagination.offset,
            limit=pagination.limit,
        )

        results = [PublicationActPackageReportShort.from_orm(r) for r in paginated_result.items]

        return PagedResponse[PublicationActPackageReportShort](
            total=paginated_result.total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=results,
        )


class ListActPackageReportsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_publication_act_package_reports"

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

        return ListActPackageReportsEndpoint(path=path)
