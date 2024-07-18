from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.dependencies import depends_simple_pagination
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PagedResponse, SimplePagination
from app.extensions.publications.dependencies import depends_publication_aoj_repository
from app.extensions.publications.models import PublicationAOJ
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.repository.publication_aoj_repository import PublicationAOJRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class ListPublicationAOJEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            pagination: SimplePagination = Depends(depends_simple_pagination),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(PublicationsPermissions.can_view_publication_aoj)
            ),
            aoj_repository: PublicationAOJRepository = Depends(depends_publication_aoj_repository),
        ) -> PagedResponse[PublicationAOJ]:
            return self._handler(aoj_repository, pagination)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[PublicationAOJ],
            summary=f"List the publication area of jurisdictions",
            description=None,
            tags=["Publication AOJ"],
        )

        return router

    def _handler(
        self,
        aoj_repository: PublicationAOJRepository,
        pagination: SimplePagination,
    ):
        paginated_result = aoj_repository.get_with_filters(
            offset=pagination.offset,
            limit=pagination.limit,
        )

        results = [PublicationAOJ.from_orm(r) for r in paginated_result.items]

        return PagedResponse[PublicationAOJ](
            total=paginated_result.total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=results,
        )


class ListPublicationAOJEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_publication_area_of_jurisdictions"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return ListPublicationAOJEndpoint(path)
