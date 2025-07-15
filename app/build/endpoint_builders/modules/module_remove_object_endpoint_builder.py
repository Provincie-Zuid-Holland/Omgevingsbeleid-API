from app.api.domains.modules.endpoints.module_remove_object_endpoint import post_module_remove_object_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ModuleRemoveObjectEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "module_remove_object"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if "{module_id}" not in builder_data.path:
            raise RuntimeError("Missing {module_id} argument in path")
        if "{object_type}" not in builder_data.path:
            raise RuntimeError("Missing {object_type} argument in path")
        if "{lineage_id}" not in builder_data.path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_module_remove_object_endpoint,
            methods=["DELETE"],
            response_model=ResponseOK,
            summary=f"Remove object from the module",
            description=None,
            tags=["Modules"],
        )
