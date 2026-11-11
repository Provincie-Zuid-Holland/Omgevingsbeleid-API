from abc import ABC, ABCMeta, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession


class ApiEvent(ABC):
    pass


class ApiListener[ApiEventType: ApiEvent](metaclass=ABCMeta):
    @abstractmethod
    async def handle_event(self, session: AsyncSession, event: ApiEventType) -> ApiEventType | None:
        pass

    def description(self) -> str:
        return self.__class__.__name__

    def get_event_type(self) -> type[ApiEventType]:
        if hasattr(self, "__orig_class__"):
            return self.__orig_class__.__args__[0]
        return self.__orig_bases__[0].__args__[0]
