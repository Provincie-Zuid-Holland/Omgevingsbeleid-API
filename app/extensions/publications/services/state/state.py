from abc import ABCMeta, abstractmethod

from pydantic import BaseModel

from app.extensions.publications.services.state.actions.action import Action


class State(BaseModel, metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def get_schema_version() -> int:
        pass

    @abstractmethod
    def get_data(self) -> dict:
        pass

    @abstractmethod
    def handle_action(self, action: Action):
        pass

    def state_dict(self) -> dict:
        result: dict = {
            "Schema_Version": self.get_schema_version(),
            "Data": self.get_data(),
        }
        return result

    class Config:
        orm_mode = True


class ActiveState(State):
    @abstractmethod
    def has_werkingsgebied(self, werkingsgebied: dict) -> bool:
        pass

    @abstractmethod
    def has_area_of_jurisdiction(self, aoj: dict) -> bool:
        pass


class StateSchema(BaseModel):
    Schema_Version: int

    class Config:
        orm_mode = True


class InitialState(State):
    @staticmethod
    def get_schema_version() -> int:
        return 1

    def get_data(self) -> dict:
        return {}

    def handle_action(self, action: Action):
        pass
