import uuid
from typing import Optional

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.dependencies import depends_simple_pagination
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PagedResponse, SimplePagination
from app.extensions.publications.dependencies import depends_publication_version_repository
from app.extensions.publications.models import PublicationVersionShort
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.repository.publication_version_repository import PublicationVersionRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class ListPublicationVersionsEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            publication_uuid: Optional[uuid.UUID] = None,
            pagination: SimplePagination = Depends(depends_simple_pagination),
            version_repository: PublicationVersionRepository = Depends(depends_publication_version_repository),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_view_publication_version,
                )
            ),
        ) -> PagedResponse[PublicationVersionShort]:
            return self._handler(
                version_repository,
                publication_uuid,
                pagination,
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[PublicationVersionShort],
            summary="List the existing Publication versions",
            description=None,
            tags=["Publication Versions"],
        )

        return router

    def _handler(
        self,
        version_repository: PublicationVersionRepository,
        publication_uuid: Optional[uuid.UUID],
        pagination: SimplePagination,
    ):
        paginated_result = version_repository.get_with_filters(
            publication_uuid=publication_uuid,
            offset=pagination.offset,
            limit=pagination.limit,
        )

        results = [PublicationVersionShort.from_orm(r) for r in paginated_result.items]

        return PagedResponse[PublicationVersionShort](
            total=paginated_result.total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=results,
        )


class ListPublicationVersionsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_publication_versions"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return ListPublicationVersionsEndpoint(path=path)
