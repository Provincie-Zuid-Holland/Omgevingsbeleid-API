from typing import List

from app.dynamic.config.models import ExtensionModel
import app.extensions.lineage_resolvers.endpoints as endpoints
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_listeners import EventListeners
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.lineage_resolvers.db.table_extensions import extend_with_attributes
from app.extensions.lineage_resolvers.models import NextObjectValidities


class LineageResolversExtension(Extension):
    def initialize(self, main_config: dict):
        extend_with_attributes()

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

    def register_models(self, models_resolver: ModelsResolver):
        models_resolver.add(
            ExtensionModel(
                id="next_object_validities",
                name="NextObjectValidities",
                pydantic_model=NextObjectValidities,
            )
        )
