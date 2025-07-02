


from app.api.domains.objects.endpoints.object_latest_endpoint import (
    ObjectLatestEndpointContext,
    view_object_latest_endpoint,
)
from app.api.domains.others.endpoints.mssql_search_endpoint import MssqlSearchEndpointContext, get_mssql_search_endpoint
from app.api.domains.others.endpoints.mssql_valid_search_endpoint import MssqlValidSearchEndpointContext, get_mssql_valid_search_endpoint
from app.api.domains.others.types import SearchObject, ValidSearchConfig, ValidSearchObject
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider
from app.core.types import Model



class MssqlSearchEndpoint(Endpoint):
    def __init__(self, path: str, search_config: SearchConfig):
        self._path: str = path
        self._search_config: SearchConfig = search_config

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            query: str,
            object_in: SearchRequestData,
            db: Session = Depends(depends_db),
            pagination: SimplePagination = Depends(depends_simple_pagination),
            user: UsersTable = Depends(depends_current_active_user),
        ) -> PagedResponse[SearchObject]:
            handler: EndpointHandler = EndpointHandler(
                db, self._search_config, pagination, query, object_in.Object_Types, object_in.Like
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
        )

        return router


class (EndpointResolver):
    def get_id(self) -> str:
        return ""

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        search_config: SearchConfig = SearchConfig(**resolver_config)

        return MssqlSearchEndpoint(
            path=path,
            search_config=search_config,
        )






class MssqlSearchEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "mssql_search"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data
        search_config: ValidSearchConfig = ValidSearchConfig(**resolver_config)

        context = MssqlSearchEndpointContext(
            search_config=search_config,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(get_mssql_search_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["POST"],
            response_model=PagedResponse[SearchObject],
            summary=f"Search for objects",
            description=None,
            tags=["Search"],
        )
