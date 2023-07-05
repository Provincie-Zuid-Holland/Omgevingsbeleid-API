import app.extensions.extended_foreign_keys.listeners as listeners
from app.dynamic.converter import Converter
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver


class ExtendedForeignKeysExtension(Extension):
    def register_listeners(
        self,
        main_config: dict,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ):
        event_dispatcher.register(listeners.ObjectStaticsExtenderListener())
        event_dispatcher.register(listeners.ObjectsExtenderListener())
        event_dispatcher.register(listeners.OptimizeSelectListener())
