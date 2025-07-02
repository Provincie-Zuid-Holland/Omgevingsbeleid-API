from app.api.domains.objects.endpoints.object_latest_endpoint import (
    ObjectLatestEndpointContext,
    view_object_latest_endpoint,
)
from app.api.domains.objects.endpoints.search_objects_endpoint import get_search_objects_endpoint
from app.api.domains.others.types import SearchObject
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider
from app.core.types import Model



class SearchObjectsEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "search"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_search_objects_endpoint,
            methods=["GET"],
            response_model=PagedResponse[SearchObject],
            summary=f"Search for objects",
            description=None,
            tags=["Search"],
        )



