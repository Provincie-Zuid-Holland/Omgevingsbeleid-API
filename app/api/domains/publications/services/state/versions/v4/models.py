import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


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


class Location(BaseModel):
    UUID: str
    Identifier: str  # basisgeo:id - also used in ow
    Gml_ID: str
    Group_ID: str
    Title: str


class Werkingsgebied(BaseModel):
    UUID: str
    Identifier: str
    Hash: str
    Object_ID: int
    Title: str
    Owner_Act: str
    Frbr: Frbr
    Locations: List[Location]

    def is_still_valid(self) -> bool:
        try:
            # If any of the "ids" are not real uuids, then its the old system which is no longer allowed
            # We will tell that this Werkingsgebied is no longer valid
            # And then we can force a new version, without manually needing to tag all "Werkingsgebieden"
            for location in self.Locations:
                _ = uuid.UUID(location.UUID)
                _ = uuid.UUID(location.Identifier)
                _ = uuid.UUID(location.Gml_ID)
                _ = uuid.UUID(location.Group_ID)
        except ValueError:
            return False
        return True


class Document(BaseModel):
    UUID: str
    Code: str
    Frbr: Frbr
    Filename: str
    Title: str
    Owner_Act: str
    Content_Type: str
    Object_ID: int
    Hash: str


class Asset(BaseModel):
    UUID: str


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
    Documents: Dict[int, Document] = Field({})
    Assets: Dict[str, Asset]
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
