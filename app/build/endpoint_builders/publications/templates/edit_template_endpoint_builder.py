from app.api.domains.publications.endpoints.templates.edit_template_endpoint import post_edit_template_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class EditPublicationTemplateEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "edit_publication_template"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        if "{template_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {template_uuid} argument in path")

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_edit_template_endpoint,
            methods=["POST"],
            response_model=ResponseOK,
            summary="Edit publication template",
            tags=["Publication Templates"],
        )
