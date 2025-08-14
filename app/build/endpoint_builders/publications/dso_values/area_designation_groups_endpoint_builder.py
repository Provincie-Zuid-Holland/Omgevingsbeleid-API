from app.api.domains.publications.endpoints.dso_value_lists.area_designation_groups_endpoint import (
    get_area_designation_groups_endpoint,
)
from app.api.domains.publications.endpoints.dso_value_lists.area_designation_types_endpoint import (
    AreaDesignationValueList,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListAreaDesignationGroupsEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_area_designation_groups"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_area_designation_groups_endpoint,
            methods=["GET"],
            response_model=AreaDesignationValueList,
            summary="List the allowed groups to use for this publication document_type",
            description=None,
            tags=["Publication Value Lists"],
        )
