import uuid
from typing import Optional

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.dependencies import depends_simple_pagination
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PagedResponse, SimplePagination
from app.extensions.publications.dependencies import depends_publication_announcement_repository
from app.extensions.publications.models.models import PublicationAnnouncementShort
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.repository.publication_announcement_repository import PublicationAnnouncementRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class ListPublicationAnnouncementsEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            act_package_uuid: Optional[uuid.UUID] = None,
            pagination: SimplePagination = Depends(depends_simple_pagination),
            repository: PublicationAnnouncementRepository = Depends(depends_publication_announcement_repository),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_view_publication_announcement,
                )
            ),
        ) -> PagedResponse[PublicationAnnouncementShort]:
            return self._handler(
                repository,
                act_package_uuid,
                pagination,
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[PublicationAnnouncementShort],
            summary="List the existing Publication announcements",
            description=None,
            tags=["Publication Announcements"],
        )

        return router

    def _handler(
        self,
        repository: PublicationAnnouncementRepository,
        act_package_uuid: Optional[uuid.UUID],
        pagination: SimplePagination,
    ):
        paginated_result = repository.get_with_filters(
            act_package_uuid=act_package_uuid,
            offset=pagination.offset,
            limit=pagination.limit,
        )

        results = [PublicationAnnouncementShort.from_orm(r) for r in paginated_result.items]

        return PagedResponse[PublicationAnnouncementShort](
            total=paginated_result.total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=results,
        )


class ListPublicationAnnouncementsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_publication_announcements"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return ListPublicationAnnouncementsEndpoint(path=path)
