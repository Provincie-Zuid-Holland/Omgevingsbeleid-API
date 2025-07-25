from typing import List
from app.api.domains.modules.endpoints.module_add_new_object_endpoint import (
    ModuleAddNewObjectEndpointContext,
    NewObjectStaticResponse,
    post_module_add_new_object_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ModuleAddNewObjectEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "module_add_new_object"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data

        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if "{module_id}" not in path:
            raise RuntimeError("Missing {module_id} argument in path")

        allowed_object_types: List[str] = resolver_config.get("allowed_object_types", [])
        if not allowed_object_types:
            raise RuntimeError("Missing allowed_object_types")

        context = ModuleAddNewObjectEndpointContext(
            object_type=api.object_type,
            allowed_object_types=allowed_object_types,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(post_module_add_new_object_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["POST"],
            response_model=NewObjectStaticResponse,
            summary="Add new object to the module",
            description=None,
            tags=["Modules"],
        )
