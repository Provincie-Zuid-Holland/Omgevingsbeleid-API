from app.api.events.listeners.retrieved_objects_event_listeners import (
    GetColumnImagesListenerBase,
    InsertHtmlImagesListenerBase,
)
from app.api.events.retrieved_module_objects_event import RetrievedModuleObjectsEvent


class InsertHtmlImagesForModuleListener(InsertHtmlImagesListenerBase[RetrievedModuleObjectsEvent]):
    pass


class GetColumnImagesForModuleObjectListener(GetColumnImagesListenerBase[RetrievedModuleObjectsEvent]):
    pass
