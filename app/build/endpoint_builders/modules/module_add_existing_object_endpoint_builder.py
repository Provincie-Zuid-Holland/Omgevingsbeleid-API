from typing import List
from app.api.domains.modules.endpoints.module_add_existing_object_endpoint import (
    ModuleAddExistingObjectEndpointContext,
    post_module_add_existing_object_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ModuleAddExistingObjectEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "module_add_existing_object"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if not "{module_id}" in builder_data.path:
            raise RuntimeError("Missing {module_id} argument in path")

        resolver_config: dict = endpoint_config.resolver_data
        allowed_object_types: List[str] = resolver_config.get("allowed_object_types", [])
        if not allowed_object_types:
            raise RuntimeError("Missing allowed_object_types")

        context = ModuleAddExistingObjectEndpointContext(
            object_type=api.object_type,
            allowed_object_types=allowed_object_types,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(post_module_add_existing_object_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Add existing object to the module",
            description=None,
            tags=["Modules"],
        )
