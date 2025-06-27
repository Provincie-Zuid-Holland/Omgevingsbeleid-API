from app.api.domains.publications.endpoints.publications.list_publications_endpoint import (
    get_list_publications_endpoint,
)
from app.api.domains.publications.types.models import Publication
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListPublicationsEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_publications"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_list_publications_endpoint,
            methods=["GET"],
            response_model=PagedResponse[Publication],
            summary="List the existing Publication",
            tags=["Publications"],
        )
