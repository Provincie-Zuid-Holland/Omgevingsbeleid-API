from typing import Dict, Generic, List, Type

from .types import BuildEventType, BuildListener


class BuildEventListeners(Generic[BuildEventType]):
    def __init__(self, listeners: List[BuildListener] = []):
        self._listeners: Dict[Type[BuildEventType], List[BuildListener]] = {}

        for listener in listeners:
            self.register(listener)

    def register(self, listener: BuildListener):
        event_type: Type[BuildEventType] = listener.get_event_type()
        if event_type not in self._listeners:
            self._listeners[event_type] = []

        self._listeners[event_type].append(listener)

    def get_listeners(self, event: BuildEventType) -> List[BuildListener]:
        event_type = type(event)
        return self._listeners.get(event_type, [])


class BuildEventManager(Generic[BuildEventType]):
    def __init__(
        self,
        event_listeners: BuildEventListeners,
    ):
        self._event_listeners: BuildEventListeners = event_listeners

    def dispatch(self, event: BuildEventType) -> BuildEventType:
        listeners: List[BuildListener] = self._event_listeners.get_listeners(event)
        if not listeners:
            return event

        for listener in listeners:
            response = listener.handle_event(event)
            if response is not None:
                event = response

        return event
