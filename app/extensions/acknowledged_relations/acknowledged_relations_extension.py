from typing import List

import app.extensions.acknowledged_relations.endpoints as endpoints
from app.dynamic.config.models import ExtensionModel
from app.dynamic.db import ObjectStaticsTable
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_listeners import EventListeners
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.acknowledged_relations.db.table_extensions.object_statics import extend_with_attributes
from app.extensions.acknowledged_relations.models import AcknowledgedRelation


class AcknowledgedRelationsExtension(Extension):
    def register_models(self, models_resolver: ModelsResolver):
        models_resolver.add(
            ExtensionModel(
                id="acknowledged_relation",
                name="AcknowledgedRelation",
                pydantic_model=AcknowledgedRelation,
            ),
        )
        # Additional orm properties for sqlalchemy
        extend_with_attributes(ObjectStaticsTable)

    def register_endpoint_resolvers(
        self,
        event_listeners: EventListeners,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return [
            endpoints.ListAcknowledgedRelationsEndpointResolver(),
            endpoints.RequestAcknowledgedRelationEndpointResolver(),
            endpoints.EditAcknowledgedRelationEndpointResolver(),
        ]
