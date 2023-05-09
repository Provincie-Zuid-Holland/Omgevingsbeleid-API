from typing import List

from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.extension import Extension
from app.dynamic.config.models import ExtensionModel
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter
import app.extensions.acknowledged_relations.endpoints as endpoints
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

    def register_endpoint_resolvers(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return [
            endpoints.ListAcknowledgedRelationsEndpointResolver(),
            endpoints.RequestAcknowledgedRelationEndpointResolver(),
            endpoints.EditAcknowledgedRelationEndpointResolver(),
        ]
