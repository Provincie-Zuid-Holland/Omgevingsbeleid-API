from typing import List

from app.dynamic.computed_fields.computed_field_resolver import ComputedFieldResolver
import app.extensions.lineage_resolvers.endpoints as endpoints
from app.dynamic.computed_fields import ComputedField, ExecutionStrategy
from app.dynamic.config.models import ExtensionModel
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_listeners import EventListeners
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.lineage_resolvers.computed_field_handlers import (
    batch_load_next_object_validities,
    load_next_object_validities,
)
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

    def register_computed_field_handlers(self, computed_field_resolver: ComputedFieldResolver):
        computed_field_resolver.add_handler("load_next_object_version", load_next_object_validities)
        computed_field_resolver.add_handler("batch_load_next_object_version", batch_load_next_object_validities)

    def register_computed_fields(self) -> List[ComputedField]:
        next_validities_field = ComputedField(
            id="next_object_version",
            model_id="next_object_validities",
            attribute_name="Next_Version",
            execution_strategy=ExecutionStrategy.SERVICE,
            handler_id="load_next_object_version",
            is_optional=True,
            is_list=False,
        )
        batch_next_validities_field = ComputedField(
            id="batch_next_object_version",
            model_id="next_object_validities",
            attribute_name="Next_Version",
            execution_strategy=ExecutionStrategy.SERVICE,
            handler_id="batch_load_next_object_version",
            is_optional=True,
            is_list=False,
        )
        return [next_validities_field, batch_next_validities_field]
