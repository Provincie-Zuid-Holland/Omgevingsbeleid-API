from app.api.domains.publications.endpoints.publications.versions.list_versions_endpoint import (
    get_list_versions_endpoint,
)
from app.api.domains.publications.types.models import PublicationVersionShort
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListPublicationVersionsEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_publication_versions"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_list_versions_endpoint,
            methods=["GET"],
            response_model=PagedResponse[PublicationVersionShort],
            summary="List the existing Publication versions",
            tags=["Publication Versions"],
        )
