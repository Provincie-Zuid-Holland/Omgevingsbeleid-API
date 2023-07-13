from typing import List

import app.extensions.relations.endpoints as endpoints
import app.extensions.relations.listeners as listeners
from app.dynamic.config.models import ExtensionModel
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.relations.models.models import ReadRelation, ReadRelationShort, WriteRelation


class RelationsExtension(Extension):
    def register_models(self, models_resolver: ModelsResolver):
        models_resolver.add(
            ExtensionModel(
                id="read_relation_short",
                name="ReadRelationShort",
                pydantic_model=ReadRelationShort,
            )
        )
        models_resolver.add(
            ExtensionModel(
                id="read_relation",
                name="ReadRelation",
                pydantic_model=ReadRelation,
            )
        )
        models_resolver.add(
            ExtensionModel(
                id="write_relation",
                name="WriteRelation",
                pydantic_model=WriteRelation,
            ),
        )

    def register_endpoint_resolvers(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return [
            endpoints.ListRelationsEndpointResolver(),
            endpoints.OverwriteRelationsEndpointResolver(),
        ]

    def register_listeners(
        self,
        main_config: dict,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ):
        event_dispatcher.register(listeners.CreateModelListener(models_resolver))
        event_dispatcher.register(listeners.RetrievedObjectsListener(converter))
        event_dispatcher.register(listeners.RetrievedModuleObjectsListener(converter))
