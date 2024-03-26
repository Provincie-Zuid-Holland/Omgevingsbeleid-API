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
from app.extensions.publications.dependencies import depends_publication_report_repository
from app.extensions.publications.enums import ReportStatusType
from app.extensions.publications.models import PublicationPackageReportShort
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.repository.publication_report_repository import PublicationReportRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class ListPackageReportsEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            package_uuid: Optional[uuid.UUID] = None,
            report_status: Optional[ReportStatusType] = None,
            pagination: SimplePagination = Depends(depends_simple_pagination),
            report_repository: PublicationReportRepository = Depends(depends_publication_report_repository),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_view_publication_package_report,
                )
            ),
        ) -> PagedResponse[PublicationPackageReportShort]:
            return self._handler(
                report_repository,
                package_uuid,
                report_status,
                pagination,
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[PublicationPackageReportShort],
            summary="List the existing Publication reports",
            description=None,
            tags=["Publication Reports"],
        )

        return router

    def _handler(
        self,
        report_repository: PublicationReportRepository,
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

        results = [PublicationPackageReportShort.from_orm(r) for r in paginated_result.items]

        return PagedResponse[PublicationPackageReportShort](
            total=paginated_result.total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=results,
        )


class ListPackageReportsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_publication_package_reports"

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

        return ListPackageReportsEndpoint(path=path)
