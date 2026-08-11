from abc import ABC, ABCMeta, abstractmethod


class BuildEvent(ABC):
    pass


class BuildListener[BuildEventType: BuildEvent](metaclass=ABCMeta):
    @abstractmethod
    def handle_event(self, event: BuildEventType) -> BuildEventType | None:
        pass

    def description(self) -> str:
        return self.__class__.__name__

    def get_event_type(self) -> type[BuildEventType]:
        if hasattr(self, "__orig_class__"):
            return self.__orig_class__.__args__[0]
        return self.__orig_bases__[0].__args__[0]
