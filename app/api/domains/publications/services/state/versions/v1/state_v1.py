
from pydantic import BaseModel, Field

from app.api.domains.publications.services.state.state import State


class Purpose(BaseModel):
    Purpose_Type: str
    Effective_Date: str | None = None
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
    Object_ID: int
    Owner_Act: str
    Frbr: Frbr


class WidData(BaseModel):
    Known_Wid_Map: dict[str, str]
    Known_Wids: list[str]


class OwObjectMap(BaseModel):
    id_mapping: dict[str, dict[str, str]]
    tekstdeel_mapping: dict[str, dict[str, str]]


class OwData(BaseModel):
    Object_Ids: list[str]
    Object_Map: OwObjectMap


class ActiveAct(BaseModel):
    Act_Frbr: Frbr
    Bill_Frbr: Frbr
    Consolidation_Purpose: Purpose
    Document_Type: str
    Procedure_Type: str
    Werkingsgebieden: dict[int, Werkingsgebied]
    Wid_Data: WidData
    Ow_Data: OwData
    Act_Text: str


class ActiveAnnouncement(BaseModel):
    Doc_Frbr: Frbr
    About_Act_Frbr: Frbr
    About_Bill_Frbr: Frbr
    Document_Type: str
    Procedure_Type: str


class StateV1(State):
    Purposes: dict[str, Purpose] = Field({})
    Acts: dict[str, ActiveAct] = Field({})
    Announcements: dict[str, ActiveAnnouncement] = Field({})

    @staticmethod
    def get_schema_version() -> int:
        return 1

    def get_data(self) -> dict:
        data: dict = self.model_dump()
        return data
