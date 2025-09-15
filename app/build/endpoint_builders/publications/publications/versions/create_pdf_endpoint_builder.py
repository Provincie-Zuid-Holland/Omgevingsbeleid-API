from app.api.domains.publications.endpoints.publications.versions.create_pdf_endpoint import post_create_pdf_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class CreatePublicationVersionPdfEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "create_publication_version_pdf"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        if "{version_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {version_uuid} argument in path")

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_create_pdf_endpoint,
            methods=["POST"],
            response_model=None,
            summary="Download Publication Version as Pdf",
            tags=["Publication Versions"],
        )
