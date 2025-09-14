from app.api.domains.publications.endpoints.area_of_jurisdictions.detail_aoj_endpoint import get_detail_aoj_endpoint
from app.api.domains.publications.endpoints.area_of_jurisdictions.edit_aoj_endpoint import post_edit_aoj_endpoint
from app.api.domains.publications.types.models import PublicationAOJ, PublicationAct
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class EditPublicationAOJEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "edit_publication_area_of_jurisdictions"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        if "{area_of_jurisdiction_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {area_of_jurisdiction_uuid} argument in path")

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_edit_aoj_endpoint,
            methods=["POST"],
            response_model=ResponseOK,
            summary="Edit a publication area of jurisdictions",
            description=None,
            tags=["Publication AOJ"],
        )
