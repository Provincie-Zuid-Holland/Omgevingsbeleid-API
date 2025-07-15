from app.api.domains.publications.endpoints.environments.detail_environment_endpoint import (
    get_detail_environment_endpoint,
)
from app.api.domains.publications.types.models import PublicationEnvironment
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class DetailPublicationEnvironmentEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "detail_publication_environment"

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
            endpoint=get_detail_environment_endpoint,
            methods=["GET"],
            response_model=PublicationEnvironment,
            summary=f"Get details of a publication environment",
            description=None,
            tags=["Publication Environments"],
        )
