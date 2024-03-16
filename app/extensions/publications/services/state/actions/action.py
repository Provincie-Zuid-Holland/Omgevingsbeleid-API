from abc import ABCMeta, abstractmethod

from pydantic import BaseModel


class Action(BaseModel, metaclass=ABCMeta):
    @abstractmethod
    def __repr__(self) -> str:
        pass
