from abc import ABC, ABCMeta, abstractmethod
from typing import Generic, Optional, Type, TypeVar


class BuildEvent(ABC):
    pass


BuildEventType = TypeVar("BuildEventType", bound=BuildEvent)


class BuildListener(Generic[BuildEventType], metaclass=ABCMeta):
    @abstractmethod
    def handle_event(self, event: BuildEventType) -> Optional[BuildEventType]:
        pass

    def description(self) -> str:
        return self.__class__.__name__

    def get_event_type(self) -> Type[BuildEventType]:
        if hasattr(self, "__orig_class__"):
            return self.__orig_class__.__args__[0]
        return self.__orig_bases__[0].__args__[0]
