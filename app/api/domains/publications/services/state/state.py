from abc import ABCMeta, abstractmethod

from pydantic import BaseModel, ConfigDict


class State(BaseModel, metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def get_schema_version() -> int:
        pass

    @abstractmethod
    def get_data(self) -> dict:
        pass

    def state_dict(self) -> dict:
        result: dict = {
            "Schema_Version": self.get_schema_version(),
            "Data": self.get_data(),
        }
        return result

    model_config = ConfigDict(from_attributes=True)


class StateSchema(BaseModel):
    Schema_Version: int
    model_config = ConfigDict(from_attributes=True)


class InitialState(State):
    @staticmethod
    def get_schema_version() -> int:
        return 4

    def get_data(self) -> dict:
        return {}
