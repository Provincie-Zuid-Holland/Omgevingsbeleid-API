from typing import List

from app.api.domains.others.endpoints.object_related_files_list_endpoint import (
    ObjectRelatedFilesListEndpointContext,
    get_object_related_files_list_endpoint,
)
from app.api.domains.others.types import ObjectRelatedFileResponse
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ObjectRelatedFilesListEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "object_related_files_list"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        context = ObjectRelatedFilesListEndpointContext(
            object_type=api.object_type,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(get_object_related_files_list_endpoint, context)

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            summary="List related files for an object",
            response_model=List[ObjectRelatedFileResponse],
            description=None,
            tags=["Object Related Files"],
        )
