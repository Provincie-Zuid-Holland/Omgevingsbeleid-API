
from typing import List
from app.api.domains.objects.endpoints import ObjectListValidLineageTreeEndpointContext, list_valid_lineage_tree_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import OrderConfig, PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider
from app.core.types import Model


class ObjectListValidLineageTreeEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "valid_list_lineage_tree"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if not "{lineage_id}" in builder_data.path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        resolver_config: dict = endpoint_config.resolver_data
        response_model: Model = models_provider.get_model(resolver_config["response_model"])

        allowed_filter_columns: List[str] = resolver_config.get("allowed_filter_columns", [])
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])

        context = ObjectListValidLineageTreeEndpointContext(
            object_type=api.object_type,
            response_config_model=response_model,
            allowed_filter_columns=allowed_filter_columns,
            order_config=order_config,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(list_valid_lineage_tree_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_model=PagedResponse[response_model.pydantic_model],
            summary=f"Get all the valid {api.object_type} of a single lineage",
            tags=[api.object_type],
        )
