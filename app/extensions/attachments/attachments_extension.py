from typing import List

import app.extensions.attachments.endpoints as endpoints
import app.extensions.attachments.listeners as listeners
from app.dynamic.config.models import ExtensionModel
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_listeners import EventListeners
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.attachments.db.tables import StorageFileTable  # # noqa
from app.extensions.attachments.models import StorageFileBasic


class AttachmentsExtension(Extension):
    def register_models(self, models_resolver: ModelsResolver):
        models_resolver.add(
            ExtensionModel(
                id="storage_file_basic",
                name="StorageFileBasic",
                pydantic_model=StorageFileBasic,
            ),
        )

    def register_endpoint_resolvers(
        self,
        event_listeners: EventListeners,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return [
            endpoints.AttachmentUploadFileEndpointResolver(),
        ]

    def register_listeners(
        self,
        main_config: dict,
        event_listeners: EventListeners,
        converter: Converter,
        models_resolver: ModelsResolver,
    ):
        event_listeners.register(listeners.AddStoreageFileRelationshipListener())
