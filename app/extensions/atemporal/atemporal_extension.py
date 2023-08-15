from typing import List

import app.extensions.atemporal.endpoints as endpoints
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver


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
            endpoints.DeleteObjectEndpointResolver(),
        ]
