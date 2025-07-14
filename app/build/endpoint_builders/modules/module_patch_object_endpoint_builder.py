from app.api.domains.modules.endpoints.module_patch_object_endpoint import (
    ModulePatchObjectContext,
    post_module_patch_object_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider
from app.core.types import Model


class ModulePatchObjectEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "module_patch_object"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if not "{module_id}" in builder_data.path:
            raise RuntimeError("Missing {module_id} argument in path")
        if not "{lineage_id}" in builder_data.path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        resolver_config: dict = endpoint_config.resolver_data
        request_model: Model = models_provider.get_model(resolver_config["request_model"])
        response_model: Model = models_provider.get_model(resolver_config["response_model"])

        context = ModulePatchObjectContext(
            object_type=api.object_type,
            request_config_model=request_model,
            response_config_model=response_model,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(post_module_patch_object_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["PATCH"],
            response_model=response_model.pydantic_model,
            summary=f"Add a new version to the {api.object_type} lineage in a module",
            description=None,
            tags=[api.object_type],
        )
