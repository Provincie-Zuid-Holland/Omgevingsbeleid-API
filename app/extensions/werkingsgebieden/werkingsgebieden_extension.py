from typing import List

import app.extensions.werkingsgebieden.listeners as listeners
from app.dynamic.computed_fields import ComputedField
from app.dynamic.computed_fields.computed_field_resolver import ComputedFieldResolver
from app.dynamic.computed_fields.models import ServiceComputedField
from app.dynamic.config.models import ExtensionModel
from app.dynamic.converter import Converter
from app.dynamic.event_listeners import EventListeners
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.werkingsgebieden.computed_field_handlers import process_werkingsgebied_related_objects
from app.extensions.werkingsgebieden.models.models import WerkingsgebiedRelatedObjects


class WerkingsgebiedenExtension(Extension):
    def __init__(self):
        super().__init__()

    def register_listeners(
        self,
        main_config: dict,
        event_listeners: EventListeners,
        converter: Converter,
        models_resolver: ModelsResolver,
    ):
        event_listeners.register(listeners.JoinWerkingsgebiedenOnCreateModelListener(models_resolver))
        event_listeners.register(listeners.LoadWerkingsgebiedOnObjectsListener())
        event_listeners.register(listeners.LoadWerkingsgebiedOnModuleObjectsListener())

    def register_models(self, models_resolver: ModelsResolver):
        models_resolver.add(
            ExtensionModel(
                id="werkingsgebied_related_objects",
                name="WerkingsgebiedRelatedObjects",
                pydantic_model=WerkingsgebiedRelatedObjects,
            )
        )

    def register_computed_fields(self) -> List[ComputedField]:
        return [
            ServiceComputedField(
                id="werkingsgebied_related_objects",
                model_id="werkingsgebied_related_objects",
                attribute_name="Related_Objects",
                is_list=False,
                is_optional=False,
                handler_id="werkingsgebied_load_related_objects",
            )
        ]

    def register_computed_field_handlers(self, computed_field_resolver: ComputedFieldResolver) -> None:
        computed_field_resolver.add_handler(
            "werkingsgebied_load_related_objects", process_werkingsgebied_related_objects
        )
