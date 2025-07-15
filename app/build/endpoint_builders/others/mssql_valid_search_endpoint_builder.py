from app.api.domains.others.endpoints.mssql_valid_search_endpoint import (
    MssqlValidSearchEndpointContext,
    get_mssql_valid_search_endpoint,
)
from app.api.domains.others.types import ValidSearchConfig, ValidSearchObject
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class MssqlValidSearchEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "mssql_valid_search"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data
        search_config: ValidSearchConfig = ValidSearchConfig(**resolver_config)

        context = MssqlValidSearchEndpointContext(
            search_config=search_config,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(get_mssql_valid_search_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["POST"],
            response_model=PagedResponse[ValidSearchObject],
            summary="Search for valid objects",
            description=None,
            tags=["Search"],
        )
