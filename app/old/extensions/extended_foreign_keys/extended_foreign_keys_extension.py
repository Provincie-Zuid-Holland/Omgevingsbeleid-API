import app.extensions.extended_foreign_keys.listeners as listeners
from app.dynamic.converter import Converter
from app.dynamic.event_listeners import EventListeners
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver


class ExtendedForeignKeysExtension(Extension):
    def register_listeners(
        self,
        main_config: dict,
        event_listeners: EventListeners,
        converter: Converter,
        models_resolver: ModelsResolver,
    ):
        event_listeners.register(listeners.ObjectStaticsExtenderListener())
        event_listeners.register(listeners.ObjectsExtenderListener())
        event_listeners.register(listeners.OptimizeSelectListener())
