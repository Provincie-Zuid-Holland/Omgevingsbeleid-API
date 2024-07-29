from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.extensions.publications.services.state.actions.action import Action
from app.extensions.publications.services.state.actions.add_announcement_action import AddAnnouncementAction
from app.extensions.publications.services.state.actions.add_publication_action import AddPublicationAction
from app.extensions.publications.services.state.actions.add_purpose_action import AddPurposeAction
from app.extensions.publications.services.state.state import ActiveState




class Purpose(BaseModel):
    Purpose_Type: str
    Effective_Date: Optional[str]
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
    Known_Wid_Map: Dict[str, str]
    Known_Wids: List[str]


class OwData(BaseModel):
    ow_objects: Dict[str, Any] = {}
    terminated_ow_ids: List[str] = []


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


class ActiveAnnouncement(BaseModel):
    Doc_Frbr: Frbr
    About_Act_Frbr: Frbr
    About_Bill_Frbr: Frbr
    Document_Type: str
    Procedure_Type: str


class StateV1(ActiveState):
    Purposes: Dict[str, Purpose] = Field({})
    Acts: Dict[str, ActiveAct] = Field({})
    Announcements: Dict[str, ActiveAnnouncement] = Field({})

    @staticmethod
    def get_schema_version() -> int:
        return 1

    def get_data(self) -> dict:
        data: dict = self.dict()
        return data

    def get_act(self, document_type: str, procedure_type: str) -> Optional[Any]:
        key: str = f"{document_type}-{procedure_type}"
        result: Optional[ActiveAct] = self.Acts.get(key)
        return result

    def handle_action(self, action: Action):
        match action:
            case AddPurposeAction():
                self._handle_add_purpose_action(action)
            case AddPublicationAction():
                self._handle_add_publication_action(action)
            case AddAnnouncementAction():
                self._handle_add_announcement_action(action)
            case _:
                raise RuntimeError(f"Action {action.__class__.__name__} is not implemented for StateV1")

    def _handle_add_purpose_action(self, action: AddPurposeAction):
        purpose = Purpose(
            Purpose_Type=action.Purpose_Type.value,
            Effective_Date=action.get_effective_date_str(),
            Work_Province_ID=action.Work_Province_ID,
            Work_Date=action.Work_Date,
            Work_Other=action.Work_Other,
        )
        frbr: str = purpose.get_frbr_work()
        self.Purposes[frbr] = purpose

    def _handle_add_publication_action(self, action: AddPublicationAction):
        active_act = ActiveAct(
            Act_Frbr=action.Act_Frbr,
            Bill_Frbr=action.Bill_Frbr,
            Consolidation_Purpose=action.Consolidation_Purpose,
            Document_Type=action.Document_Type,
            Procedure_Type=action.Procedure_Type,
            Werkingsgebieden=action.Werkingsgebieden,
            Wid_Data=action.Wid_Data,
            Ow_Data=action.Ow_Data,
            Act_Text=action.Act_Text,
        )
        key: str = f"{action.Document_Type}-{action.Procedure_Type}"
        self.Acts[key] = active_act

    def _handle_add_announcement_action(self, action: AddAnnouncementAction):
        active_announcement = ActiveAnnouncement(
            Doc_Frbr=action.Doc_Frbr,
            About_Act_Frbr=action.About_Act_Frbr,
            About_Bill_Frbr=action.About_Bill_Frbr,
            Document_Type=action.Document_Type,
            Procedure_Type=action.Procedure_Type,
        )
        key: str = f"{action.Document_Type}-{action.Procedure_Type}"
        self.Announcements[key] = active_announcement
