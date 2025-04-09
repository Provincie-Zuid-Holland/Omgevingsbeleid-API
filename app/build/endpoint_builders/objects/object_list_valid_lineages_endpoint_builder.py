
from typing import List
from app.api.domains.objects.endpoints import ObjectListValidLineagesEndpointContext, list_valid_lineages_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import OrderConfig, PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider
from app.core.types import Model


class ObjectListValidLineagesEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "valid_list_lineages"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data
        response_model: Model = models_provider.get_model(resolver_config["response_model"])

        allowed_filter_columns: List[str] = resolver_config.get("allowed_filter_columns", [])
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])

        context = ObjectListValidLineagesEndpointContext(
            object_type=api.object_type,
            response_config_model=response_model,
            allowed_filter_columns=allowed_filter_columns,
            order_config=order_config,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(list_valid_lineages_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_type=PagedResponse[response_model.pydantic_model],
            summary=f"Get all the valid {api.object_type} lineages and shows the latest object of each",
            tags=[api.object_type],
        )
