from typing import List
from app.api.domains.objects.endpoints.acknowledged_relation_request_endpoint import (
    AcknowledgedRelationRequestEndpointContext,
    get_acknowledged_relation_request_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class AcknowledgedRelationRequestEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "request_acknowledged_relation"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data
        allowed_object_types: List[str] = resolver_config.get("allowed_object_types", [])
        if not allowed_object_types:
            raise RuntimeError("Missing required config allowed_object_types")

        context = AcknowledgedRelationRequestEndpointContext(
            object_type=api.object_type,
            allowed_object_types=allowed_object_types,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(get_acknowledged_relation_request_endpoint, context)

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["POST"],
            response_model=ResponseOK,
            summary="Request an acknowledged relation to another object",
            description=None,
            tags=[api.object_type],
        )
