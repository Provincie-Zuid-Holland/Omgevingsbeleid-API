from enum import Enum
from typing import Dict

from pydantic import BaseModel, Field

from app.extensions.publications.services.state.actions import Action
from app.extensions.publications.services.state.actions.add_werkingsgebied import AddWerkingsgebiedAction
from app.extensions.publications.services.state.state import State


class ConsolidationStatus(str, Enum):
    consolidated = "consolidated"
    withdrawn = "withdrawn"


class Werkingsgebied(BaseModel):
    UUID: str
    Object_ID: int
    Work: str
    Expression_Version: str
    Act_Work: str
    Act_Expression_Version: str


class StateV1(State):
    Werkingsgebieden: Dict[int, Werkingsgebied] = Field({})

    @staticmethod
    def get_schema_version() -> int:
        return 1

    def get_data(self) -> dict:
        data: dict = self.dict()
        return data

    def handle_action(self, action: Action):
        match action:
            case AddWerkingsgebiedAction():
                self._handle_add_werkinggsgebied_action(action)
            case _:
                raise RuntimeError(f"Action {action.__class__.__name__} is not implemented for StateV1")

    def _handle_add_werkinggsgebied_action(self, action: AddWerkingsgebiedAction):
        werkingsgebied: Werkingsgebied = Werkingsgebied(
            UUID=str(action.UUID),
            Object_ID=action.Object_ID,
            Work=action.Work,
            Expression_Version=action.Expression_Version,
            Act_Work=action.Act_Frbr.get_work(),
            Act_Expression_Version=action.Act_Frbr.get_expression_version(),
        )
        self.Werkingsgebieden[werkingsgebied.Object_ID] = werkingsgebied
