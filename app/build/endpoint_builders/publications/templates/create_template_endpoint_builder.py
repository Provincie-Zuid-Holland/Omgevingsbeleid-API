from app.api.domains.publications.endpoints.templates.create_template_endpoint import (
    TemplateCreatedResponse,
    post_create_template_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class CreatePublicationTemplateEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "create_publication_template"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_create_template_endpoint,
            methods=["POST"],
            response_model=TemplateCreatedResponse,
            summary="Create new publication template",
            tags=["Publication Templates"],
        )
