from abc import ABCMeta, abstractmethod

from .state import State


class StateUpgrader(metaclass=ABCMeta):
    @abstractmethod
    def upgrade(self, state: State) -> State:
        pass
