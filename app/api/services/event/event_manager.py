from typing import Any, Dict, Generic, List, Type

from sqlalchemy.orm import Session

from .types import EventType, Listener


class EventListeners(Generic[EventType]):
    def __init__(self):
        self._listeners: Dict[Type[EventType], List[Listener]] = {}

    def register(self, listener: Listener):
        event_type: Type[EventType] = listener.get_event_type()
        if not event_type in self._listeners:
            self._listeners[event_type] = []

        self._listeners[event_type].append(listener)

    def get_listeners(self, event: EventType) -> List[Listener]:
        event_type = type(event)
        return self._listeners.get(event_type, [])


class EventManager(Generic[EventType]):
    def __init__(
        self,
        event_listeners: EventListeners,
        db: Session,
    ):
        self._event_listeners: EventListeners = event_listeners
        self._db: Session = db

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
