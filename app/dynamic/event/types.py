from abc import ABC, ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

from sqlalchemy.orm import Session


class Event(ABC):
    def __init__(self):
        self._db: Optional[Session] = None

    def provide_db(self, db: Optional[Session]):
        self._db = db

    def get_db(self) -> Session:
        if self._db is None:
            raise RuntimeError("db not set for event")
        return self._db


EventType = TypeVar("EventType", bound=Event)


class Listener(Generic[EventType], metaclass=ABCMeta):
    @abstractmethod
    def handle_event(self, event: EventType) -> EventType:
        pass

    def description(self) -> str:
        return self.__class__.__name__


@dataclass
class NoPayload:
    pass
