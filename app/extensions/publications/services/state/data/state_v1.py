from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field

from app.extensions.publications.services.state.actions.action import Action
from app.extensions.publications.services.state.actions.add_area_of_jurisdiction_action import (
    AddAreaOfJurisdictionAction,
)
from app.extensions.publications.services.state.actions.add_purpose_action import AddPurposeAction
from app.extensions.publications.services.state.actions.consolidate_werkingsgebied_action import (
    ConsolidateWerkingsgebiedAction,
)
from app.extensions.publications.services.state.state import ActiveState


class ConsolidationStatus(str, Enum):
    consolidated = "consolidated"
    withdrawn = "withdrawn"


class Purpose(BaseModel):
    Purpose_Type: str
    Effective_Date: str
    Work_Province_ID: str
    Work_Date: str
    Work_Other: str

    def get_frbr_work(self) -> str:
        result: str = f"/join/id/proces/{self.Work_Province_ID}/{self.Work_Date}/{self.Work_Other}"
        return result


class Werkingsgebied(BaseModel):
    UUID: str
    Consolidation_Status: ConsolidationStatus
    Consolidation_Purpose: Purpose
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


class Bill(BaseModel):
    Work: str
    Expression_Version: str


class Act(BaseModel):
    Work: str
    Expression_Version: str


class StateV1(ActiveState):
    Werkingsgebieden: Dict[int, Werkingsgebied] = Field({})
    Area_Of_Jurisdiction: Optional[AreaOfJurisdiction] = Field(None)
    Purposes: Dict[str, Purpose] = Field({})
    Active_Acts: Dict[str, Act] = Field({})

    @staticmethod
    def get_schema_version() -> int:
        return 1

    def get_data(self) -> dict:
        data: dict = self.dict()
        return data

    def has_werkingsgebied(self, werkingsgebied: dict) -> bool:
        object_id: int = werkingsgebied["Object_ID"]
        maybe_werkingsgebied: Optional[Werkingsgebied] = self.Werkingsgebieden.get(object_id, None)
        if maybe_werkingsgebied is None:
            return False
        result: bool = str(werkingsgebied["UUID"]) == maybe_werkingsgebied.UUID
        return result

    def has_area_of_jurisdiction(self, aoj: dict) -> bool:
        if self.Area_Of_Jurisdiction is None:
            return False
        result: bool = str(aoj["UUID"]) == self.Area_Of_Jurisdiction.UUID
        return result

    def handle_action(self, action: Action):
        match action:
            case AddPurposeAction():
                self._handle_add_purpose_action(action)
            case ConsolidateWerkingsgebiedAction():
                self._handle_consolidate_werkinggsgebied_action(action)
            case AddAreaOfJurisdictionAction():
                self._handle_add_area_of_jurisdiction_action(action)
            case _:
                raise RuntimeError(f"Action {action.__class__.__name__} is not implemented for StateV1")

    def _handle_add_purpose_action(self, action: AddPurposeAction):
        purpose: Purpose = Purpose(
            Purpose_Type=action.Purpose_Type.value,
            Effective_Date=action.get_effective_date_str(),
            Work_Province_ID=action.Work_Province_ID,
            Work_Date=action.Work_Date,
            Work_Other=action.Work_Other,
        )
        frbr: str = purpose.get_frbr_work()
        self.Purposes[frbr] = purpose

    def _handle_consolidate_werkinggsgebied_action(self, action: ConsolidateWerkingsgebiedAction):
        # @todo: guard that Object_ID can not be added if one is already widrawn
        werkingsgebied: Werkingsgebied = Werkingsgebied(
            UUID=str(action.UUID),
            Consolidation_Status=ConsolidationStatus.consolidated,
            Consolidation_Purpose=Purpose(
                Purpose_Type=action.Consolidation_Purpose.Purpose_Type,
                Effective_Date=action.Consolidation_Purpose.Effective_Date.strftime("%Y-%m-%d"),
                Work_Province_ID=action.Consolidation_Purpose.Work_Province_ID,
                Work_Date=action.Consolidation_Purpose.Work_Date,
                Work_Other=action.Consolidation_Purpose.Work_Other,
            ),
            Object_ID=action.Object_ID,
            Work=action.Work,
            Expression_Version=action.Expression_Version,
            Act_Work=action.Act_Frbr.get_work(),
            Act_Expression_Version=action.Act_Frbr.get_expression_version(),
        )
        self.Werkingsgebieden[werkingsgebied.Object_ID] = werkingsgebied

    def _handle_add_area_of_jurisdiction_action(self, action: AddAreaOfJurisdictionAction):
        # @todo: guard that we do not add duplicates
        aoj: AreaOfJurisdiction = AreaOfJurisdiction(
            UUID=str(action.UUID),
            Consolidation_Status=ConsolidationStatus.consolidated,
            Administrative_Borders_ID=action.Administrative_Borders_ID,
            Act_Work=action.Act_Frbr.get_work(),
            Act_Expression_Version=action.Act_Frbr.get_expression_version(),
        )
        self.Area_Of_Jurisdiction = aoj
