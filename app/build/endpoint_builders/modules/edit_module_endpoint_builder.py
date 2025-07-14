from app.api.domains.modules.endpoints.edit_module_endpoint import post_edit_module_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class EditModuleEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "edit_module"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if not "{module_id}" in builder_data.path:
            raise RuntimeError("Missing {module_id} argument in path")

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_edit_module_endpoint,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Edit module",
            description=None,
            tags=["Modules"],
        )
