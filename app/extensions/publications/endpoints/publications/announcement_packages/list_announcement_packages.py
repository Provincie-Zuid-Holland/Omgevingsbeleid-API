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
from app.extensions.publications.dependencies import depends_publication_announcement_package_repository
from app.extensions.publications.models import PublicationPackage
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.repository.publication_announcement_package_repository import (
    PublicationAnnouncementPackageRepository,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class ListPublicationAnnouncementPackagesEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            announcement_uuid: Optional[uuid.UUID] = None,
            pagination: SimplePagination = Depends(depends_simple_pagination),
            package_repository: PublicationAnnouncementPackageRepository = Depends(
                depends_publication_announcement_package_repository
            ),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_view_publication_announcement_package,
                )
            ),
        ) -> PagedResponse[PublicationPackage]:
            return self._handler(
                package_repository,
                announcement_uuid,
                pagination,
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[PublicationPackage],
            summary="List the existing publication announcement packages of a publication version",
            description=None,
            tags=["Publication Announcement Packages"],
        )

        return router

    def _handler(
        self,
        package_repository: PublicationAnnouncementPackageRepository,
        announcement_uuid: Optional[uuid.UUID],
        pagination: SimplePagination,
    ):
        paginated_result = package_repository.get_with_filters(
            announcement_uuid=announcement_uuid,
            offset=pagination.offset,
            limit=pagination.limit,
        )

        results = [PublicationPackage.from_orm(r) for r in paginated_result.items]

        return PagedResponse[PublicationPackage](
            total=paginated_result.total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=results,
        )


class ListPublicationAnnouncementPackagesEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_publication_announcement_packages"

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

        return ListPublicationAnnouncementPackagesEndpoint(
            path=path,
        )
