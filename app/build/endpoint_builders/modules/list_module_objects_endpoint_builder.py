from typing import Dict

from app.api.domains.modules.endpoints.list_module_objects_endpoint import (
    ListModuleObjectsEndpointContext,
    ModuleObjectsResponseBase,
    get_list_module_objects_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import OrderConfig, PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.build.services.module_objects_to_models_parser import ModuleObjectsToModelsParser
from app.core.services.models_provider import ModelsProvider


class ListModuleObjectsEndpointBuilder(EndpointBuilder):
    def __init__(self, module_objects_to_models_parser: ModuleObjectsToModelsParser):
        self._module_objects_to_models_parser = module_objects_to_models_parser

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
        model_map: Dict[str, str] = resolver_config["model_map"]

        context = ListModuleObjectsEndpointContext(
            order_config=order_config,
            builder_data=builder_data,
            model_map=model_map,
        )
        endpoint = self._inject_context(get_list_module_objects_endpoint, context)

        dynamic_types = self._module_objects_to_models_parser.get_types(context.model_map)
        response_model = self._module_objects_to_models_parser.update_response_model(
            "ModuleObjectsResponse", ModuleObjectsResponseBase, dynamic_types
        )

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_model=PagedResponse[response_model],
            summary="List latest module objects filtered by e.g. owner uuid, object type or minimum status",
            description=None,
            tags=["Modules"],
        )
