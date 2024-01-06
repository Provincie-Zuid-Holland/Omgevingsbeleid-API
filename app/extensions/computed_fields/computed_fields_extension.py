from app.dynamic.converter import Converter
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.computed_fields.listeners.computed_fields_listener import InsertComputedFieldsListener


class ComputedFieldsExtension(Extension):
    def register_listeners(
        self,
        main_config: dict,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ):
        event_dispatcher.register(InsertComputedFieldsListener())
