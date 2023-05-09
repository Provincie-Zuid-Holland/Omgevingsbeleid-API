from typing import List

from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import EndpointResolver
import app.extensions.atemporal.endpoints as endpoints


class AtemporalExtension(Extension):
    def register_endpoint_resolvers(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return [
            endpoints.CreateObjectEndpointResolver(),
            endpoints.EditObjectEndpointResolver(),
        ]
