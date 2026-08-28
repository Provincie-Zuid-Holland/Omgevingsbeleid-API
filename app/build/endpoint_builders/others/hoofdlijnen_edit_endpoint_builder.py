from app.api.domains.others.endpoints import post_hoofdlijnen_edit_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class EditHoofdlijnenEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "edit_hoofdlijn"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_hoofdlijnen_edit_endpoint,
            methods=["POST"],
            response_model=ResponseOK,
            summary="Edit an existing hoofdlijn",
            description=None,
            tags=["Hoofdlijn"],
        )
