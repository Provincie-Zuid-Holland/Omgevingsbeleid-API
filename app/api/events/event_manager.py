from collections.abc import Sequence

from sqlalchemy.orm import Session

from .types import ApiEvent, ApiListener


class ApiEventListeners[ApiEventType: ApiEvent]:
    def __init__(self, listeners: Sequence[ApiListener] = ()):
        self._listeners: dict[type[ApiEventType], list[ApiListener]] = {}

        for listener in listeners:
            self.register(listener)

    def register(self, listener: ApiListener):
        event_type: type[ApiEventType] = listener.get_event_type()
        if event_type not in self._listeners:
            self._listeners[event_type] = []

        self._listeners[event_type].append(listener)

    def get_listeners(self, event: ApiEventType) -> list[ApiListener]:
        event_type = type(event)
        return self._listeners.get(event_type, [])


class ApiEventManager[ApiEventType: ApiEvent]:
    def __init__(
        self,
        event_listeners: ApiEventListeners,
    ):
        self._event_listeners: ApiEventListeners = event_listeners

    def dispatch(self, session: Session, event: ApiEventType) -> ApiEventType:
        listeners: list[ApiListener] = self._event_listeners.get_listeners(event)
        if not listeners:
            return event

        for listener in listeners:
            response = listener.handle_event(session, event)
            if response is not None:
                event = response

        return event
