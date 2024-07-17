from typing import List

import app.extensions.lineage_resolvers.endpoints as endpoints
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_listeners import EventListeners
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver


class LineageResolversExtension(Extension):
    def register_endpoint_resolvers(
        self,
        event_listeners: EventListeners,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return [
            endpoints.EditObjectStaticEndpointResolver(),
            endpoints.ValidListLineagesEndpointResolver(),
            endpoints.ValidListLineageTreeEndpointResolver(),
            endpoints.ObjectVersionEndpointResolver(),
            endpoints.ObjectLatestEndpointResolver(),
            endpoints.ListAllLatestObjectsResolver(),
            endpoints.ObjectCountsEndpointResolver(),
        ]
