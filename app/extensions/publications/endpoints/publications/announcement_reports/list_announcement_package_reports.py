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
from app.extensions.publications.dependencies import depends_publication_announcement_report_repository
from app.extensions.publications.enums import ReportStatusType
from app.extensions.publications.models.models import PublicationAnnouncementPackageReportShort
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.repository.publication_announcement_report_repository import (
    PublicationAnnouncementReportRepository,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class ListAnnouncementPackageReportsEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            announcement_package_uuid: Optional[uuid.UUID] = None,
            report_status: Optional[ReportStatusType] = None,
            pagination: SimplePagination = Depends(depends_simple_pagination),
            report_repository: PublicationAnnouncementReportRepository = Depends(
                depends_publication_announcement_report_repository
            ),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_view_publication_announcement_package_report,
                )
            ),
        ) -> PagedResponse[PublicationAnnouncementPackageReportShort]:
            return self._handler(
                report_repository,
                announcement_package_uuid,
                report_status,
                pagination,
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[PublicationAnnouncementPackageReportShort],
            summary="List the existing Publication Announcement reports",
            description=None,
            tags=["Publication Announcement Reports"],
        )

        return router

    def _handler(
        self,
        report_repository: PublicationAnnouncementReportRepository,
        announcement_package_uuid: Optional[uuid.UUID],
        report_status: Optional[ReportStatusType],
        pagination: SimplePagination,
    ):
        paginated_result = report_repository.get_with_filters(
            announcement_package_uuid=announcement_package_uuid,
            report_status=report_status,
            offset=pagination.offset,
            limit=pagination.limit,
        )

        results = [PublicationAnnouncementPackageReportShort.from_orm(r) for r in paginated_result.items]

        return PagedResponse[PublicationAnnouncementPackageReportShort](
            total=paginated_result.total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=results,
        )


class ListAnnouncementPackageReportsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_publication_announcement_package_reports"

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

        return ListAnnouncementPackageReportsEndpoint(path=path)
