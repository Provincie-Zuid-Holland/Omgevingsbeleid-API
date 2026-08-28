from app.api.domains.others.endpoints import delete_hoofdlijnen_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class DeleteHoofdlijnenEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "delete_hoofdlijn"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=delete_hoofdlijnen_endpoint,
            methods=["DELETE"],
            response_model=ResponseOK,
            summary="Delete an existing hoofdlijn",
            description=None,
            tags=["Hoofdlijn"],
        )
