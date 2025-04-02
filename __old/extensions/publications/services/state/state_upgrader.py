import uuid
from abc import ABCMeta, abstractmethod

from .state import State


class StateUpgrader(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def get_input_schema_version() -> int:
        pass

    @abstractmethod
    def upgrade(self, environment_uuid: uuid.UUID, old_state: State) -> State:
        pass
