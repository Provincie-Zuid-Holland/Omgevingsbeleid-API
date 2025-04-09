
from app.api.domains.objects.endpoints import ObjectListAllLatestEndpointContext, GenericObjectShort, list_all_latest_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import OrderConfig, PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ObjectListAllLatestEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_all_latest_objects"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])

        context = ObjectListAllLatestEndpointContext(
            object_type=api.object_type,
            order_config=order_config,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(list_all_latest_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_type=PagedResponse[GenericObjectShort],
            summary=f"List all objects filterable in short format",
            tags=["Search"],
        )
