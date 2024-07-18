from typing import Any, Dict, Generic, List

from .event.types import EventType, Listener


class EventListeners(Generic[EventType]):
    def __init__(self):
        self._listeners: Dict[EventType, List[Listener]] = {}

    def register(self, listener: Listener):
        event_type = self._get_event_type(listener)
        if not event_type in self._listeners:
            self._listeners[event_type] = []

        self._listeners[event_type].append(listener)

    def get_listeners(self, event: EventType) -> List[Listener]:
        event_type = type(event)
        return self._listeners.get(event_type, [])

    def _get_event_type(self, listener: Listener) -> Any:
        if hasattr(listener, "__orig_class__"):
            return listener.__orig_class__.__args__[0]
        return listener.__orig_bases__[0].__args__[0]
