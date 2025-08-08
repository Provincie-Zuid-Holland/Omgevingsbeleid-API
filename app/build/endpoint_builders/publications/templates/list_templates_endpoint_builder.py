from app.api.domains.publications.endpoints.templates.list_templates_endpoint import get_list_templates_endpoint
from app.api.domains.publications.types.models import PublicationTemplate
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListPublicationTemplatesEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_publication_templates"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_list_templates_endpoint,
            methods=["GET"],
            response_model=PagedResponse[PublicationTemplate],
            summary="List the publication templates",
            tags=["Publication Templates"],
        )
