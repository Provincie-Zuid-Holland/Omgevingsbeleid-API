from abc import ABC, ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Generic, Optional, Type, TypeVar

from sqlalchemy.orm import Session


class Event(ABC):
    # @todo: Remove DB from here and inject it in the listeners that need it
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
    def handle_event(self, event: EventType) -> Optional[EventType]:
        pass

    def description(self) -> str:
        return self.__class__.__name__

    def get_event_type(self) -> Type[EventType]:
        if hasattr(self, "__orig_class__"):
            return self.__orig_class__.__args__[0]
        return self.__orig_bases__[0].__args__[0]


@dataclass
class NoPayload:
    pass
