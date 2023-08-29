from typing import List

import app.extensions.atemporal.endpoints as endpoints
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.extension import Extension


class AtemporalExtension(Extension):
    def register_endpoint_resolvers(self) -> List[EndpointResolver]:
        return [
            endpoints.CreateObjectEndpointResolver(),
            endpoints.EditObjectEndpointResolver(),
            endpoints.DeleteObjectEndpointResolver(),
        ]
