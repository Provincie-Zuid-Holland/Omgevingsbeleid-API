from typing import List


from app.dynamic.extension import Extension
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.converter import Converter
import app.extensions.regulations.endpoints as endpoints
import app.extensions.regulations.listeners as listeners


class RegulationsExtension(Extension):
    def register_endpoint_resolvers(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return [
            endpoints.CreateRegulationEndpointResolver(),
            endpoints.EditRegulationEndpointResolver(),
            endpoints.ListRegulationsEndpointResolver(),
            endpoints.OverwriteObjectRegulationsEndpointResolver(),
            endpoints.ListObjectRegulationsEndpointResolver(),
        ]

    def register_listeners(
        self,
        main_config: dict,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ):
        event_dispatcher.register(listeners.RegulationsCreateModelListener())
        event_dispatcher.register(listeners.RegulationsRetrievedObjectsListener())