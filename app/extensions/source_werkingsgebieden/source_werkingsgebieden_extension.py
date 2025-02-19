from typing import List

import app.extensions.source_werkingsgebieden.endpoints as endpoints
import app.extensions.source_werkingsgebieden.listeners as listeners
from app.dynamic.config.models import ExtensionModel
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_listeners import EventListeners
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.source_werkingsgebieden.models.models import Werkingsgebied


class SourceWerkingsgebiedenExtension(Extension):
    def register_models(self, models_resolver: ModelsResolver):
        models_resolver.add(
            ExtensionModel(
                id="werkingsgebied",
                name="Werkingsgebied",
                pydantic_model=Werkingsgebied,
            ),
        )

    def register_endpoint_resolvers(
        self,
        event_listeners: EventListeners,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return [
            endpoints.ListWerkingsgebiedenEndpointResolver(),
            endpoints.ListObjectsInGeoEndpointResolver(),
            endpoints.ListObjectsByGeometryEndpointResolver(),
        ]

    def register_listeners(
        self,
        main_config: dict,
        event_listeners: EventListeners,
        converter: Converter,
        models_resolver: ModelsResolver,
    ):
        event_listeners.register(listeners.AddWerkingsgebiedenRelationshipListener())
