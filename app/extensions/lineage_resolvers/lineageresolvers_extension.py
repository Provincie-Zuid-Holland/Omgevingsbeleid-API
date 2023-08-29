from typing import List

import app.extensions.lineage_resolvers.endpoints as endpoints
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.extension import Extension


class LineageResolversExtension(Extension):
    def register_endpoint_resolvers(self) -> List[EndpointResolver]:
        return [
            endpoints.EditObjectStaticEndpointResolver(),
            endpoints.ValidListLineagesEndpointResolver(),
            endpoints.ValidListLineageTreeEndpointResolver(),
            endpoints.ObjectVersionEndpointResolver(),
            endpoints.ObjectLatestEndpointResolver(),
            endpoints.ListAllLatestObjectsResolver(),
        ]
