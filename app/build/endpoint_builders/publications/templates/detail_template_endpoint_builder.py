from app.api.domains.publications.endpoints.templates.detail_template_endpoint import get_detail_template_endpoint
from app.api.domains.publications.types.models import PublicationTemplate
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class DetailPublicationTemplateEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "detail_publication_template"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if "{template_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {template_uuid} argument in path")

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_detail_template_endpoint,
            methods=["GET"],
            response_model=PublicationTemplate,
            summary=f"Get details of a publication template",
            tags=["Publication Templates"],
        )
