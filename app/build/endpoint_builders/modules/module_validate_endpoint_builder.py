from app.api.domains.modules.endpoints.module_validate_endpoint import get_module_validate_endpoint
from app.api.domains.modules.services.validate_module_service import ValidateModuleResult
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ModuleValidateEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "validate_module"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_module_validate_endpoint,
            methods=["GET"],
            response_model=ValidateModuleResult,
            summary="Validate the objects in a module",
            description=None,
            tags=["Modules"],
        )
