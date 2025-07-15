from app.api.domains.publications.endpoints.environments.edit_environment_endpoint import post_edit_environment_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class EditPublicationEnvironmentEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "edit_publication_environment"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if "{environment_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {environment_uuid} argument in path")

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_edit_environment_endpoint,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Edit publication environment",
            description=None,
            tags=["Publication Environments"],
        )
