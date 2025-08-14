from app.api.domains.others.endpoints.mssql_search_endpoint import MssqlSearchEndpointContext, get_mssql_search_endpoint
from app.api.domains.others.types import SearchObject, ValidSearchConfig
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class MssqlSearchEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "mssql_search"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data
        search_config: ValidSearchConfig = ValidSearchConfig(**resolver_config)

        context = MssqlSearchEndpointContext(
            search_config=search_config,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(get_mssql_search_endpoint, context)

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["POST"],
            response_model=PagedResponse[SearchObject],
            summary="Search for objects",
            description=None,
            tags=["Search"],
        )
