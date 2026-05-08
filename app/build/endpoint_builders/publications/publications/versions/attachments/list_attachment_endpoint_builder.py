from typing import List

from app.api.domains.publications.endpoints.publications.versions.attachments.list_attachments_endpoint import (
    get_list_attachments_endpoint,
)
from app.api.domains.publications.types.models import AttachmentShort
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import EndpointBuilder, ConfiguredFastapiEndpoint
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services import ModelsProvider


class ListPublicationVersionAttachmentEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_publication_version_attachment"

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
            endpoint=get_list_attachments_endpoint,
            methods=["GET"],
            summary="List attachments for a Publication Version",
            response_model=List[AttachmentShort],
            description=None,
            tags=["Publication Versions"],
        )
