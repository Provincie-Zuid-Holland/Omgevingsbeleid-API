from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Purpose(BaseModel):
    Purpose_Type: str
    Effective_Date: Optional[str] = None
    Work_Province_ID: str
    Work_Date: str
    Work_Other: str

    def get_frbr_work(self) -> str:
        result: str = f"/join/id/proces/{self.Work_Province_ID}/{self.Work_Date}/{self.Work_Other}"
        return result


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
    Identifier: str
    Hash: str
    Object_ID: int
    Title: str
    Owner_Act: str
    Frbr: Frbr

    @model_validator(mode="before")
    def default_identifier_to_uuid(cls, values):
        if not values.get("Identifier"):
            values["Identifier"] = str(values["UUID"])
        return values


class WidData(BaseModel):
    Known_Wid_Map: Dict[str, str]
    Known_Wids: List[str]


class OwData(BaseModel):
    Ow_Objects: Dict[str, Any] = Field({}, alias="ow_objects")
    Terminated_Ow_Ids: List[str] = Field([], alias="terminated_ow_ids")
    model_config = ConfigDict(populate_by_name=True)


class ActiveAct(BaseModel):
    Act_Frbr: Frbr
    Bill_Frbr: Frbr
    Consolidation_Purpose: Purpose
    Document_Type: str
    Procedure_Type: str
    Werkingsgebieden: Dict[int, Werkingsgebied]
    Wid_Data: WidData
    Ow_Data: OwData
    Act_Text: str
    Publication_Version_UUID: str


class ActiveAnnouncement(BaseModel):
    Doc_Frbr: Frbr
    About_Act_Frbr: Frbr
    About_Bill_Frbr: Frbr
    Document_Type: str
    Procedure_Type: str
