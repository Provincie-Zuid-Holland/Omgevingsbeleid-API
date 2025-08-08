from app.api.domains.modules.endpoints.module_patch_status_endpoint import post_module_patch_status_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ModulePatchStatusEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "module_patch_status"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_module_patch_status_endpoint,
            methods=["PATCH"],
            response_model=ResponseOK,
            summary="Patch the status of the module",
            description=None,
            tags=["Modules"],
        )
