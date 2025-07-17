from typing import Optional
from app.api.domains.modules.endpoints.module_object_version_endpoint import (
    ModuleObjectVersionEndpointContext,
    view_module_object_version_endpoint,
)
from app.api.domains.modules.types import ModuleStatusCode
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider
from app.core.types import Model


class ModuleObjectVersionEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "module_object_version"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if "{module_id}" not in builder_data.path:
            raise RuntimeError("Missing {module_id} argument in path")
        if "{object_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {object_uuid} argument in path")

        resolver_config: dict = endpoint_config.resolver_data
        response_model: Model = models_provider.get_model(resolver_config["response_model"])
        require_auth: bool = resolver_config.get("require_auth", True)

        minimum_status: Optional[ModuleStatusCode] = None
        requested_minimum_status: Optional[str] = resolver_config.get("minimum_status", None)
        if requested_minimum_status:
            try:
                minimum_status = ModuleStatusCode(requested_minimum_status)
            except ValueError:
                raise RuntimeError("Invalid module status code: {requested_minimum_status}")

        context = ModuleObjectVersionEndpointContext(
            object_type=api.object_type,
            minimum_status=minimum_status,
            require_auth=require_auth,
            response_config_model=response_model,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(view_module_object_version_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_model=response_model.pydantic_model,
            summary=f"Get specific {api.object_type} by uuid in a module",
            description=None,
            tags=[api.object_type],
            operation_id=self._to_operation_id(builder_data.path, "get"),
        )
