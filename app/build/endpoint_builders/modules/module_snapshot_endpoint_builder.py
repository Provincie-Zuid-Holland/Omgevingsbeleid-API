from app.api.domains.modules.endpoints.module_snapshot_endpoint import ModuleSnapshot, get_module_snapshot_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ModuleSnapshotEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "module_snapshot"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_module_snapshot_endpoint,
            methods=["GET"],
            response_model=ModuleSnapshot,
            summary="Get snapshot of a module by status id",
            description=None,
            tags=["Modules"],
        )
