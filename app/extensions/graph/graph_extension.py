from typing import List

import app.extensions.graph.endpoints as endpoints
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.extension import Extension


class GraphExtension(Extension):
    def register_endpoint_resolvers(self) -> List[EndpointResolver]:
        return [
            endpoints.FullGraphEndpointResolver(),
            endpoints.ObjectGraphEndpointResolver(),
        ]
