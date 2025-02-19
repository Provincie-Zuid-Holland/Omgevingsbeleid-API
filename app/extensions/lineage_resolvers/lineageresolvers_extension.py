from typing import List

import app.extensions.lineage_resolvers.endpoints as endpoints
from app.dynamic.config.models import ComputedField, ExtensionModel
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_listeners import EventListeners
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.lineage_resolvers.db.next_object_version import build_composite_next_version
from app.extensions.lineage_resolvers.models import NextObjectValidities


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

    def register_models(self, models_resolver: ModelsResolver):
        models_resolver.add(
            ExtensionModel(
                id="next_object_validities",
                name="NextObjectValidities",
                pydantic_model=NextObjectValidities,
            )
        )

    def register_computed_fields(self) -> List[ComputedField]:
        next_validities_query = build_composite_next_version()
        next_validities_field = ComputedField(
            id="next_object_validities",
            model_id="next_object_validities",
            attribute_name="Next_Version",
            action=next_validities_query,
            is_optional=True,
        )
        return [next_validities_field]
