from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_publication
from app.extensions.publications.models import Publication
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.tables.tables import PublicationTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class DetailPublicationEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            publication: PublicationTable = Depends(depends_publication),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_view_publication,
                ),
            ),
        ) -> Publication:
            result: Publication = Publication.model_validate(publication)
            return result

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=Publication,
            summary=f"Get details of a publication",
            description=None,
            tags=["Publications"],
        )

        return router


class DetailPublicationEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "detail_publication"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{publication_uuid}" in path:
            raise RuntimeError("Missing {publication_uuid} argument in path")

        return DetailPublicationEndpoint(
            path=path,
        )
