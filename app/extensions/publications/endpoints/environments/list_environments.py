from typing import Optional

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_simple_pagination
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PagedResponse, SimplePagination
from app.extensions.publications.dependencies import depends_publication_environment_repository
from app.extensions.publications.models import PublicationEnvironment
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.repository.publication_environment_repository import PublicationEnvironmentRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class ListPublicationEnvironmentsEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            is_active: Optional[bool] = None,
            pagination: SimplePagination = Depends(depends_simple_pagination),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_view_publication_environment,
                )
            ),
            environment_repository: PublicationEnvironmentRepository = Depends(
                depends_publication_environment_repository
            ),
        ) -> PagedResponse[PublicationEnvironment]:
            return self._handler(environment_repository, is_active, pagination)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[PublicationEnvironment],
            summary=f"List the publication environments",
            description=None,
            tags=["Publication Environments"],
        )

        return router

    def _handler(
        self,
        environment_repository: PublicationEnvironmentRepository,
        is_active: Optional[bool],
        pagination: SimplePagination,
    ):
        paginated_result = environment_repository.get_with_filters(
            is_active=is_active,
            offset=pagination.offset,
            limit=pagination.limit,
        )

        results = [PublicationEnvironment.from_orm(r) for r in paginated_result.items]

        return PagedResponse[PublicationEnvironment](
            total=paginated_result.total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=results,
        )


class ListPublicationEnvironmentsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_publication_environments"

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

        return ListPublicationEnvironmentsEndpoint(path)
