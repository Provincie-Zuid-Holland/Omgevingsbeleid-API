from app.api.domains.modules.endpoints.list_modules_endpoint import (
    ListModulesEndpointContext,
    get_list_modules_endpoint,
)
from app.api.domains.modules.types import Module
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import OrderConfig, PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListModulesEndpointResolverBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_modules"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])

        context = ListModulesEndpointContext(
            order_config=order_config,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(get_list_modules_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_model=PagedResponse[Module],
            summary=f"List the modules",
            description=None,
            tags=["Modules"],
        )
