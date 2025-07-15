from app.api.domains.publications.endpoints.publications.versions.detail_version_endpoint import (
    get_detail_version_endpoint,
)
from app.api.domains.publications.types.models import PublicationVersion
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class DetailPublicationVersionEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "detail_publication_version"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if "{version_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {version_uuid} argument in path")

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_detail_version_endpoint,
            methods=["GET"],
            response_model=PublicationVersion,
            summary="Get details of a publication version",
            tags=["Publication Versions"],
        )
