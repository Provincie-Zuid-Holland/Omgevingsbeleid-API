from app.api.domains.modules.endpoints.module_get_object_context_endpoint import (
    ModuleObjectContext,
    get_module_get_object_context_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ModuleGetObjectContextEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "module_get_object_context"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_module_get_object_context_endpoint,
            methods=["GET"],
            response_model=ModuleObjectContext,
            summary="Get context of object in the module",
            description=None,
            tags=["Modules"],
        )
