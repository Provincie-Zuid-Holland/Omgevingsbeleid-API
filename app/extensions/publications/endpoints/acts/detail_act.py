from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_publication_act
from app.extensions.publications.models.models import PublicationAct
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.tables.tables import PublicationActTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class DetailActEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            act: PublicationActTable = Depends(depends_publication_act),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_view_publication_act,
                )
            ),
        ) -> PublicationAct:
            result: PublicationAct = PublicationAct.from_orm(act)
            return result

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PublicationAct,
            summary=f"Get details of a publication act",
            description=None,
            tags=["Publication Acts"],
        )

        return router


class DetailPublicationActEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "detail_publication_act"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{act_uuid}" in path:
            raise RuntimeError("Missing {act_uuid} argument in path")

        return DetailActEndpoint(path)
