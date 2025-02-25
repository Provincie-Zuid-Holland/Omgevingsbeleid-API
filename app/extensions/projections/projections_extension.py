from typing import List

import app.extensions.projections.endpoints as endpoints
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_listeners import EventListeners
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver


class ProjectionsExtension(Extension):
    def register_endpoint_resolvers(
        self,
        event_listeners: EventListeners,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return [
            endpoints.CreateGraphsEndpointResolver(),
            endpoints.ViewGraphEndpointResolver(),
            endpoints.DetailObjectEndpointResolver(),
        ]
