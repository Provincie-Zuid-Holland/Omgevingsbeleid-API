from typing import List

import app.extensions.werkingsgebieden.listeners as listeners
from app.dynamic.config.models import ExtensionModel
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_listeners import EventListeners
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver


class WerkingsgebiedenExtension(Extension):
    def register_listeners(
        self,
        main_config: dict,
        event_listeners: EventListeners,
        converter: Converter,
        models_resolver: ModelsResolver,
    ):
        event_listeners.register(listeners.CreateModelListener(models_resolver))
        event_listeners.register(listeners.RetrievedObjectsListener(converter))
        event_listeners.register(listeners.RetrievedModuleObjectsListener(converter))
