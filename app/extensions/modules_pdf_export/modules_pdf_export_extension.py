from app.dynamic.extension import Extension
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter
import app.extensions.modules_pdf_export.listeners as listeners


class ModulesPdfExportExtension(Extension):
    def register_listeners(
        self,
        main_config: dict,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ):
        event_dispatcher.register(
            listeners.PdfExportModuleStatusChangedListener(main_config)
        )
