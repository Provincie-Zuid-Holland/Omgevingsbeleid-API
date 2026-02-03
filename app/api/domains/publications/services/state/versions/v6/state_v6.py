from typing import Any, Dict, Optional

from pydantic import Field

from app.api.domains.publications.services.state.state import State
from app.api.domains.publications.services.state.versions.v6 import models
from app.api.domains.publications.services.state.versions.v6.actions import (
    Action,
    AddAnnouncementAction,
    AddPublicationAction,
    AddPurposeAction,
)


class StateV6(State):
    Purposes: Dict[str, models.Purpose] = Field({})
    Acts: Dict[str, models.ActiveAct] = Field({})
    Announcements: Dict[str, models.ActiveAnnouncement] = Field({})

    @staticmethod
    def get_schema_version() -> int:
        return 6

    def get_data(self) -> dict:
        data: dict = self.model_dump()
        return data

    def get_act(self, document_type: str, procedure_type: str) -> Optional[Any]:
        key: str = f"{document_type}-{procedure_type}"
        result: Optional[models.ActiveAct] = self.Acts.get(key)
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
                raise RuntimeError(f"Action {action.__class__.__name__} is not implemented for StateV4")

    def _handle_add_purpose_action(self, action: AddPurposeAction):
        purpose = models.Purpose(
            Purpose_Type=action.Purpose_Type.value,
            Effective_Date=action.get_effective_date_str(),
            Work_Province_ID=action.Work_Province_ID,
            Work_Date=action.Work_Date,
            Work_Other=action.Work_Other,
        )
        frbr: str = purpose.get_frbr_work()
        self.Purposes[frbr] = purpose

    def _handle_add_publication_action(self, action: AddPublicationAction):
        active_act = models.ActiveAct(
            Act_Frbr=action.Act_Frbr,
            Bill_Frbr=action.Bill_Frbr,
            Consolidation_Purpose=action.Consolidation_Purpose,
            Document_Type=action.Document_Type,
            Procedure_Type=action.Procedure_Type,
            Gios=action.Gios,
            Gebiedengroepen=action.Gebiedengroepen,
            Gebiedsaanwijzingen=action.Gebiedsaanwijzingen,
            Documents=action.Documents,
            Assets=action.Assets,
            Wid_Data=action.Wid_Data,
            Ow_State=action.Ow_State,
            Act_Text=action.Act_Text,
            Publication_Version_UUID=action.Publication_Version_UUID,
        )
        key: str = f"{action.Document_Type}-{action.Procedure_Type}"
        self.Acts[key] = active_act

    def _handle_add_announcement_action(self, action: AddAnnouncementAction):
        active_announcement = models.ActiveAnnouncement(
            Doc_Frbr=action.Doc_Frbr,
            About_Act_Frbr=action.About_Act_Frbr,
            About_Bill_Frbr=action.About_Bill_Frbr,
            Document_Type=action.Document_Type,
            Procedure_Type=action.Procedure_Type,
        )
        key: str = f"{action.Document_Type}-{action.Procedure_Type}"
        self.Announcements[key] = active_announcement
