from typing import Any, Dict, Generic, List, Optional

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from .event.types import EventType, Listener


class EventDispatcher(Generic[EventType]):
    def __init__(self):
        self._db: Optional[Session] = None
        self._task_runner: Optional[BackgroundTasks] = None
        self._listeners: Dict[EventType, List[Listener]] = {}

    def provide_db(self, db: Session):
        self._db = db

    def provide_task_runner(self, task_runner: BackgroundTasks):
        self._task_runner = task_runner

    def register(self, listener: Listener):
        event_type = self._get_event_type(listener)
        if not event_type in self._listeners:
            self._listeners[event_type] = []

        self._listeners[event_type].append(listener)

    def dispatch(self, event: EventType) -> EventType:
        event_type = type(event)
        if not event_type in self._listeners:
            return event

        if self._db:
            print(f"\n\n\n------------- EventDispatcher DB HASH_KEY: {self._db.hash_key}\n\n\n")
            event.provide_db(self._db)
        if self._task_runner:
            event.provide_task_runner(self._task_runner)

        for listener in self._listeners[event_type]:
            print(f"\n\n\n------------- Run event: {type(listener).__name__}\n\n\n")
            response = listener.handle_event(event)
            if response is not None:
                event = response

        return event

    def _get_event_type(self, listener: Listener) -> Any:
        if hasattr(listener, "__orig_class__"):
            return listener.__orig_class__.__args__[0]
        return listener.__orig_bases__[0].__args__[0]


main_event_dispatcher = EventDispatcher()
