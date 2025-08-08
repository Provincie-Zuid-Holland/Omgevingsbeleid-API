from app.api.domains.publications.endpoints.publications.edit_publication_endpoint import post_edit_publication_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class EditPublicationEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "edit_publication"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        if "{publication_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {publication_uuid} argument in path")

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_edit_publication_endpoint,
            methods=["POST"],
            response_model=ResponseOK,
            summary="Edit an existing publication",
            tags=["Publications"],
        )
