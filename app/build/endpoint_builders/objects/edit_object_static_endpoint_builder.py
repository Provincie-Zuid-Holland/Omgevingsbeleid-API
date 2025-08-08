from typing import Type

from pydantic import BaseModel
from app.api.domains.objects.endpoints import EditObjectStaticEndpointContext, edit_object_static_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class EditObjectStaticEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "edit_object_static"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        if "{lineage_id}" not in builder_data.path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        resolver_config: dict = endpoint_config.resolver_data

        request_type: Type[BaseModel] = models_provider.get_pydantic_model(resolver_config["request_model"])
        result_type: Type[BaseModel] = models_provider.get_pydantic_model(resolver_config["result_model"])

        context = EditObjectStaticEndpointContext(
            object_type=api.object_type,
            request_type=request_type,
            result_type=result_type,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(edit_object_static_endpoint, context)
        endpoint = self._overwrite_argument_type(endpoint, "object_in", request_type)

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["POST"],
            response_model=ResponseOK,
            summary="Edit static data of an object",
            tags=[api.object_type],
        )
