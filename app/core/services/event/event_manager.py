from typing import Dict, Generic, List, Type

from sqlalchemy.orm import Session

from .types import EventType, Listener


class EventListeners(Generic[EventType]):
    def __init__(self, listeners: List[Listener] = []):
        self._listeners: Dict[Type[EventType], List[Listener]] = {}

        for listener in listeners:
            self.register(listener)

    def register(self, listener: Listener):
        event_type: Type[EventType] = listener.get_event_type()
        if event_type not in self._listeners:
            self._listeners[event_type] = []

        self._listeners[event_type].append(listener)

    def get_listeners(self, event: EventType) -> List[Listener]:
        event_type = type(event)
        return self._listeners.get(event_type, [])


class EventManager(Generic[EventType]):
    def __init__(
        self,
        event_listeners: EventListeners,
    ):
        self._event_listeners: EventListeners = event_listeners

    def dispatch(self, session: Session, event: EventType) -> EventType:
        listeners: List[Listener] = self._event_listeners.get_listeners(event)
        if not listeners:
            return event

        for listener in listeners:
            response = listener.handle_event(session, event)
            if response is not None:
                event = response

        return event
