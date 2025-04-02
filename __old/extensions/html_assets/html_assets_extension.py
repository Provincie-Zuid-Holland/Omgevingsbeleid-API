import app.extensions.html_assets.listeners as listeners
from app.dynamic.converter import Converter
from app.dynamic.event_listeners import EventListeners
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.html_assets.db.tables import AssetsTable  # noqa


class HtmlAssetsExtension(Extension):
    def register_listeners(
        self,
        main_config: dict,
        event_listeners: EventListeners,
        converter: Converter,
        models_resolver: ModelsResolver,
    ):
        event_listeners.register(listeners.ExtractHtmlImagesListener())
        event_listeners.register(listeners.InsertHtmlImagesForModuleListener())
        event_listeners.register(listeners.InsertHtmlImagesForObjectListener())
        event_listeners.register(listeners.StoreImagesListener())
        event_listeners.register(listeners.GetImagesForModuleListener())
        event_listeners.register(listeners.GetImagesForObjectListener())
