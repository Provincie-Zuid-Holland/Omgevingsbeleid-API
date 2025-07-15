from app.api.domains.publications.endpoints.publications.detail_publication_endpoint import (
    get_detail_publication_endpoint,
)
from app.api.domains.publications.types.models import Publication
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class DetailPublicationEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "detail_publication"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if "{publication_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {publication_uuid} argument in path")

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_detail_publication_endpoint,
            methods=["GET"],
            response_model=Publication,
            summary=f"Get details of a publication",
            tags=["Publications"],
        )
