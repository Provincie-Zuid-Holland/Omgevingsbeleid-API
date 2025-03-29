from typing import Any, Generic, List, Optional

from sqlalchemy.orm import Session

from app.dynamic.event_listeners import EventListeners

from .event.types import EventType, Listener


class EventDispatcher(Generic[EventType]):
    def __init__(
        self,
        event_listeners: EventListeners,
        db: Optional[Session] = None,
    ):
        self._event_listeners: EventListeners = event_listeners
        self._db: Optional[Session] = db

    def dispatch(self, event: EventType) -> EventType:
        listeners: List[Listener] = self._event_listeners.get_listeners(event)
        if not listeners:
            return event

        if self._db:
            event.provide_db(self._db)

        for listener in listeners:
            response = listener.handle_event(event)
            if response is not None:
                event = response

        return event

    def _get_event_type(self, listener: Listener) -> Any:
        if hasattr(listener, "__orig_class__"):
            return listener.__orig_class__.__args__[0]
        return listener.__orig_bases__[0].__args__[0]
