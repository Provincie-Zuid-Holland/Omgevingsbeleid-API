from app.api.domains.modules.endpoints.module_edit_object_context_endpoint import (
    post_module_edit_object_context_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
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
    ) -> ConfiguredFastapiEndpoint:
        if "{module_id}" not in builder_data.path:
            raise RuntimeError("Missing {module_id} argument in path")
        if "{object_type}" not in builder_data.path:
            raise RuntimeError("Missing {object_type} argument in path")
        if "{lineage_id}" not in builder_data.path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_module_edit_object_context_endpoint,
            methods=["POST"],
            response_model=ResponseOK,
            summary="Edit context of object in the module",
            description=None,
            tags=["Modules"],
        )
