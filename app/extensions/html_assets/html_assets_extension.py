from app.dynamic.extension import Extension
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter
import app.extensions.html_assets.listeners as listeners
from app.extensions.html_assets.db.tables import AssetsTable  # noqa


class HtmlAssetsExtension(Extension):
    def register_listeners(
        self,
        main_config: dict,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ):
        event_dispatcher.register(listeners.ExtractHtmlImagesListener())
        event_dispatcher.register(listeners.InsertHtmlImagesListener())
        event_dispatcher.register(listeners.StoreImagesListener())
        event_dispatcher.register(listeners.GetImagesListener())
