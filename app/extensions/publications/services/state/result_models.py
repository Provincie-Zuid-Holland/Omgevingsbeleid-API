from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel


class ConsolidationStatus(str, Enum):
    consolidated = "consolidated"
    withdrawn = "withdrawn"


class AreaOfJurisdiction(BaseModel):
    UUID: str
    Consolidation_Status: ConsolidationStatus
    Administrative_Borders_ID: str
    Act_Work: str
    Act_Expression_Version: str


class Frbr(BaseModel):
    Work_Province_ID: str
    Work_Country: str
    Work_Date: str
    Work_Other: str
    Expression_Language: str
    Expression_Date: str
    Expression_Version: int


class Werkingsgebied(BaseModel):
    UUID: str
    Object_ID: int
    Owner_Act: str
    Frbr: Frbr


class Purpose(BaseModel):
    Purpose_Type: str
    Effective_Date: Optional[str]
    Work_Province_ID: str
    Work_Date: str
    Work_Other: str

    def get_frbr_work(self) -> str:
        result: str = f"/join/id/proces/{self.Work_Province_ID}/{self.Work_Date}/{self.Work_Other}"
        return result


class Bill(BaseModel):
    Work: str
    Expression_Version: str


class Act(BaseModel):
    Work: str
    Expression_Version: str


class WidData(BaseModel):
    Known_Wid_Map: Dict[str, str]
    Known_Wids: List[str]


class OwData(BaseModel):
    pass


class ActiveAct(BaseModel):
    Act_Frbr: Frbr
    Bill_Frbr: Frbr
    Consolidation_Purpose: Purpose
    Document_Type: str
    Procedure_Type: str
    Werkingsgebieden: Dict[int, Werkingsgebied]
    Wid_Data: WidData
    Ow_Data: OwData
