from typing import List
from app.api.domains.objects.endpoints.relations_overwrite_endpoint import (
    RelationsOverwriteEndpointContext,
    post_relations_overwrite_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class RelationsOverwriteEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "overwrite_relations"

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
        allowed_object_types_relations: List[str] = resolver_config.get("allowed_object_types_relations", [])
        if not allowed_object_types_relations:
            raise RuntimeError("Missing required config allowed_object_types_relations")

        context = RelationsOverwriteEndpointContext(
            object_type=api.object_type,
            allowed_object_types_relations=allowed_object_types_relations,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(post_relations_overwrite_endpoint, context)

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["PUT"],
            response_model=ResponseOK,
            summary=f"Overwrite all relations of the given {api.object_type} lineage",
            description=None,
            tags=[api.object_type],
        )
