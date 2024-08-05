from abc import ABCMeta, abstractmethod

from pydantic import BaseModel


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

    class Config:
        orm_mode = True


class StateSchema(BaseModel):
    Schema_Version: int

    class Config:
        orm_mode = True


class InitialState(State):
    @staticmethod
    def get_schema_version() -> int:
        return 2

    def get_data(self) -> dict:
        return {}
