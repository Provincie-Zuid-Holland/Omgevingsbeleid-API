from typing import List

import app.extensions.areas.listeners as listeners
from app.dynamic.config.models import ExtensionModel
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.areas.db.tables import AreasTable  # # noqa

from .models import AreaBasic, WerkingsgebiedStatics


class AreasExtension(Extension):
    def register_models(self, models_resolver: ModelsResolver):
        models_resolver.add(
            ExtensionModel(
                id="area_basic",
                name="AreaBasic",
                pydantic_model=AreaBasic,
            ),
        )
        models_resolver.add(
            ExtensionModel(
                id="werkingsgebied_statics",
                name="WerkingsgebiedStatics",
                pydantic_model=WerkingsgebiedStatics,
            )
        )

    def register_endpoint_resolvers(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return []

    def register_listeners(
        self,
        main_config: dict,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ):
        event_dispatcher.register(listeners.AddAreasRelationshipListener())
        event_dispatcher.register(listeners.ChangeAreaListener())
