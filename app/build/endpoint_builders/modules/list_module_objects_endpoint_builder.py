from app.api.domains.modules.endpoints.list_module_objects_endpoint import (
    ListModuleObjectsEndpointContext,
    ModuleObjectsResponse,
    get_list_module_objects_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import OrderConfig, PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListModuleObjectsEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_module_objects"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])

        context = ListModuleObjectsEndpointContext(
            object_type=api.object_type,
            order_config=order_config,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(get_list_module_objects_endpoint, context)

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_model=PagedResponse[ModuleObjectsResponse],
            summary="List latest module objects filtered by e.g. owner uuid, object type or minimum status",
            description=None,
            tags=["Modules"],
        )
