from abc import ABC, ABCMeta, abstractmethod
from typing import Generic, Optional, Type, TypeVar

from sqlalchemy.orm import Session


class ApiEvent(ABC):
    pass


ApiEventType = TypeVar("ApiEventType", bound=ApiEvent)


class ApiListener(Generic[ApiEventType], metaclass=ABCMeta):
    @abstractmethod
    def handle_event(self, session: Session, event: ApiEventType) -> Optional[ApiEventType]:
        pass

    def description(self) -> str:
        return self.__class__.__name__

    def get_event_type(self) -> Type[ApiEventType]:
        if hasattr(self, "__orig_class__"):
            return self.__orig_class__.__args__[0]
        return self.__orig_bases__[0].__args__[0]
