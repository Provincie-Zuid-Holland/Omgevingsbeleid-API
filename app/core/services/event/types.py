from abc import ABC, ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Generic, Optional, Type, TypeVar


class Event(ABC):
    pass


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
