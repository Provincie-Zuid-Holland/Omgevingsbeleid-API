from app.api.domains.others.endpoints import post_hoofdlijnen_create_endpoint
from app.api.domains.others.endpoints.hoofdlijnen_create_endpoint import HoofdlijnCreatedResponse
from app.api.domains.publications.endpoints.area_of_jurisdictions.create_aoj_endpoint import (
    AOJCreatedResponse,
    post_create_aoj_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class CreateHoofdlijnEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "create_hoofdlijn"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_hoofdlijnen_create_endpoint,
            methods=["POST"],
            response_model=HoofdlijnCreatedResponse,
            summary="Create new hoofdlijn",
            description=None,
            tags=["Hoofdlijn"],
        )
