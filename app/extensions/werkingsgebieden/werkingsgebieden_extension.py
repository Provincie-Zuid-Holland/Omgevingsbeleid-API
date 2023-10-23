from typing import List

import app.extensions.werkingsgebieden.endpoints as endpoints
import app.extensions.werkingsgebieden.listeners as listeners
from app.dynamic.config.models import ExtensionModel
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.werkingsgebieden.models.models import Werkingsgebied


class WerkingsgebiedenExtension(Extension):
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
        event_dispatcher: EventDispatcher,
        converter: Converter,
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
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ):
        event_dispatcher.register(listeners.AddWerkingsgebiedenRelationshipListener())
