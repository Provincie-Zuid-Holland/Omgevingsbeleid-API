from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field

from app.extensions.publications.services.state.actions.action import Action
from app.extensions.publications.services.state.actions.consolidate_area_of_jurisdiction_action import (
    ConsolidateAreaOfJurisdictionAction,
)
from app.extensions.publications.services.state.actions.consolidate_werkingsgebied_action import (
    ConsolidateWerkingsgebiedAction,
)
from app.extensions.publications.services.state.state import State


class ConsolidationStatus(str, Enum):
    consolidated = "consolidated"
    withdrawn = "withdrawn"


class Werkingsgebied(BaseModel):
    UUID: str
    Consolidation_Status: ConsolidationStatus
    Object_ID: int
    Work: str
    Expression_Version: str
    Act_Work: str
    Act_Expression_Version: str


class AreaOfJurisdiction(BaseModel):
    UUID: str
    Consolidation_Status: ConsolidationStatus
    Administrative_Borders_ID: str
    Act_Work: str
    Act_Expression_Version: str


class StateV1(State):
    Werkingsgebieden: Dict[int, Werkingsgebied] = Field({})
    AreaOfJurisdictions: List[AreaOfJurisdiction] = Field([])

    @staticmethod
    def get_schema_version() -> int:
        return 1

    def get_data(self) -> dict:
        data: dict = self.dict()
        return data

    def handle_action(self, action: Action):
        match action:
            case ConsolidateWerkingsgebiedAction():
                self._handle_consolidate_werkinggsgebied_action(action)
            case ConsolidateAreaOfJurisdictionAction():
                self._handle_consolidate_area_of_jurisdiction_action(action)
            case _:
                raise RuntimeError(f"Action {action.__class__.__name__} is not implemented for StateV1")

    def _handle_consolidate_werkinggsgebied_action(self, action: ConsolidateWerkingsgebiedAction):
        # @todo: guard that Object_ID can not be added if one is already widrawn
        werkingsgebied: Werkingsgebied = Werkingsgebied(
            UUID=str(action.UUID),
            Consolidation_Status=ConsolidationStatus.consolidated,
            Object_ID=action.Object_ID,
            Work=action.Work,
            Expression_Version=action.Expression_Version,
            Act_Work=action.Act_Frbr.get_work(),
            Act_Expression_Version=action.Act_Frbr.get_expression_version(),
        )
        self.Werkingsgebieden[werkingsgebied.Object_ID] = werkingsgebied

    def _handle_consolidate_area_of_jurisdiction_action(self, action: ConsolidateAreaOfJurisdictionAction):
        # @todo: guard that we do not add duplicates
        aoj: AreaOfJurisdiction = AreaOfJurisdiction(
            UUID=str(action.UUID),
            Consolidation_Status=ConsolidationStatus.consolidated,
            Administrative_Borders_ID=action.Administrative_Borders_ID,
            Act_Work=action.Act_Frbr.get_work(),
            Act_Expression_Version=action.Act_Frbr.get_expression_version(),
        )
        self.AreaOfJurisdictions.append(aoj)
