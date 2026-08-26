from app.api.domains.others.endpoints import post_hoofdlijnen_search_endpoint
from app.api.domains.others.types import Hoofdlijn
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class SearchHoofdlijnenEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "search_hoofdlijn"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_hoofdlijnen_search_endpoint,
            methods=["POST"],
            response_model=PagedResponse[Hoofdlijn],
            summary="Search for hoofdlijnen",
            description=None,
            tags=["Hoofdlijn"],
        )
