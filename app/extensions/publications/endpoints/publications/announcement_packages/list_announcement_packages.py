import uuid
from typing import Optional

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.dependencies import depends_sorted_pagination_curried
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import OrderConfig, PagedResponse, SortedPagination
from app.extensions.publications.dependencies import depends_publication_announcement_package_repository
from app.extensions.publications.enums import PackageType
from app.extensions.publications.models import PublicationPackage
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.repository.publication_announcement_package_repository import (
    PublicationAnnouncementPackageRepository,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class ListPublicationAnnouncementPackagesEndpoint(Endpoint):
    def __init__(self, path: str, order_config: OrderConfig):
        self._path: str = path
        self._order_config: OrderConfig = order_config

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            announcement_uuid: Optional[uuid.UUID] = None,
            package_type: Optional[PackageType] = None,
            pagination: SortedPagination = Depends(depends_sorted_pagination_curried(self._order_config)),
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
                package_type,
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
        package_type: Optional[PackageType],
        pagination: SortedPagination,
    ):
        paginated_result = package_repository.get_with_filters(
            announcement_uuid=announcement_uuid, package_type=package_type, pagination=pagination
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
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])

        return ListPublicationAnnouncementPackagesEndpoint(path=path, order_config=order_config)
