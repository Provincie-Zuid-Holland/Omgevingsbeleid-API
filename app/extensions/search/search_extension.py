from typing import List

import app.extensions.search.endpoints as endpoints
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.extension import Extension


class SearchExtension(Extension):
    def register_endpoint_resolvers(self) -> List[EndpointResolver]:
        return [
            endpoints.SearchEndpointResolver(),
        ]
