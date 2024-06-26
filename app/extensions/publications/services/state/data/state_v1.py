from typing import Dict, Optional

from pydantic import Field

from app.extensions.publications.services.state import result_models
from app.extensions.publications.services.state.actions.action import Action
from app.extensions.publications.services.state.actions.add_announcement_action import AddAnnouncementAction
from app.extensions.publications.services.state.actions.add_publication_action import AddPublicationAction
from app.extensions.publications.services.state.actions.add_purpose_action import AddPurposeAction
from app.extensions.publications.services.state.state import ActiveState


class StateV1(ActiveState):
    Purposes: Dict[str, result_models.Purpose] = Field({})
    Acts: Dict[str, result_models.ActiveAct] = Field({})
    Announcements: Dict[str, result_models.ActiveAnnouncement] = Field({})

    @staticmethod
    def get_schema_version() -> int:
        return 1

    def get_data(self) -> dict:
        data: dict = self.dict()
        return data

    def get_act(self, document_type: str, procedure_type: str) -> Optional[result_models.ActiveAct]:
        key: str = f"{document_type}-{procedure_type}"
        result: Optional[result_models.ActiveAct] = self.Acts.get(key)
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
        purpose = result_models.Purpose(
            Purpose_Type=action.Purpose_Type.value,
            Effective_Date=action.get_effective_date_str(),
            Work_Province_ID=action.Work_Province_ID,
            Work_Date=action.Work_Date,
            Work_Other=action.Work_Other,
        )
        frbr: str = purpose.get_frbr_work()
        self.Purposes[frbr] = purpose

    def _handle_add_publication_action(self, action: AddPublicationAction):
        active_act = result_models.ActiveAct(
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
        active_announcement = result_models.ActiveAnnouncement(
            Doc_Frbr=action.Doc_Frbr,
            About_Act_Frbr=action.About_Act_Frbr,
            About_Bill_Frbr=action.About_Bill_Frbr,
            Document_Type=action.Document_Type,
            Procedure_Type=action.Procedure_Type,
        )
        key: str = f"{action.Document_Type}-{action.Procedure_Type}"
        self.Announcements[key] = active_announcement
