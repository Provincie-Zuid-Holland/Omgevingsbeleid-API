from collections.abc import Sequence

from .types import BuildEvent, BuildListener


class BuildEventListeners[BuildEventType: BuildEvent]:
    def __init__(self, listeners: Sequence[BuildListener] = ()):
        self._listeners: dict[type[BuildEventType], list[BuildListener]] = {}

        for listener in listeners:
            self.register(listener)

    def register(self, listener: BuildListener):
        event_type: type[BuildEventType] = listener.get_event_type()
        if event_type not in self._listeners:
            self._listeners[event_type] = []

        self._listeners[event_type].append(listener)

    def get_listeners(self, event: BuildEventType) -> list[BuildListener]:
        event_type = type(event)
        return self._listeners.get(event_type, [])


class BuildEventManager[BuildEventType: BuildEvent]:
    def __init__(
        self,
        event_listeners: BuildEventListeners,
    ):
        self._event_listeners: BuildEventListeners = event_listeners

    def dispatch(self, event: BuildEventType) -> BuildEventType:
        listeners: list[BuildListener] = self._event_listeners.get_listeners(event)
        if not listeners:
            return event

        for listener in listeners:
            response = listener.handle_event(event)
            if response is not None:
                event = response

        return event
