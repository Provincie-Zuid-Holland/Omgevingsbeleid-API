from typing import Dict, Union

from pydantic import BaseModel

from app.api.domains.modules.endpoints.module_overview_endpoint import (
    view_module_overview_endpoint,
    ViewModuleOverviewEndpointContext,
    ModuleOverviewResponse,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.build.services.model_dynamic_type_builder import ModelDynamicTypeBuilder
from app.core.services.models_provider import ModelsProvider


class ModuleOverviewEndpointBuilder(EndpointBuilder):
    def __init__(self, model_dynamic_type_builder: ModelDynamicTypeBuilder):
        self._model_dynamic_type_builder: ModelDynamicTypeBuilder = model_dynamic_type_builder

    def get_id(self) -> str:
        return "module_overview"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        if "{module_id}" not in builder_data.path:
            raise RuntimeError("Missing {module_id} argument in path")

        resolver_config: dict = endpoint_config.resolver_data
        model_map: Dict[str, str] = resolver_config["model_map"]
        response_model_name: str = resolver_config["response_model_name"]

        union_object_type: Union[BaseModel] = self._model_dynamic_type_builder.build_object_union_type(model_map)
        response_type = ModuleOverviewResponse[union_object_type]
        response_type.__name__ = response_model_name

        context = ViewModuleOverviewEndpointContext(
            builder_data=builder_data,
            model_map=model_map,
        )
        endpoint = self._inject_context(view_module_overview_endpoint, context)

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_model=response_type,
            summary="Get overview of a module",
            description=None,
            tags=["Modules"],
        )
