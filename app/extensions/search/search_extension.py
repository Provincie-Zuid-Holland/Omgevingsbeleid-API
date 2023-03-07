from typing import List


from app.dynamic.extension import Extension
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.converter import Converter
import app.extensions.search.endpoints as endpoints


class SearchExtension(Extension):
    def register_endpoint_resolvers(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return [
            endpoints.SearchEndpointResolver(),
        ]
