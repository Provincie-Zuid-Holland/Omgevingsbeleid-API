from app.api.domains.modules.endpoints.module_edit_object_context_endpoint import (
    post_module_edit_object_context_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ModuleEditObjectContextEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "module_edit_object_context"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if not "{module_id}" in builder_data.path:
            raise RuntimeError("Missing {module_id} argument in path")
        if not "{object_type}" in builder_data.path:
            raise RuntimeError("Missing {object_type} argument in path")
        if not "{lineage_id}" in builder_data.path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_module_edit_object_context_endpoint,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Edit context of object in the module",
            description=None,
            tags=["Modules"],
        )
