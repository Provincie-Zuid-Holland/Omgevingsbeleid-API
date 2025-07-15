from typing import List
from app.api.domains.objects.endpoints.relations_list_endpoint import (
    RelationsListEndpointContext,
    get_relations_list_endpoint,
)
from app.api.domains.objects.types import ReadRelation
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class RelationsListEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_relations"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if "{lineage_id}" not in builder_data.path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        resolver_config: dict = endpoint_config.resolver_data

        context = RelationsListEndpointContext(
            object_type=api.object_type,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(get_relations_list_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_model=List[ReadRelation],
            summary=f"Get all relation codes of the given {api.object_type} lineage",
            description=None,
            tags=[api.object_type],
        )
