from typing import Any

from pydantic import Field

from app.api.domains.publications.services.state.state import State
from app.api.domains.publications.services.state.versions.v8 import models
from app.api.domains.publications.services.state.versions.v8.actions import (
    Action,
    AddAnnouncementAction,
    AddPublicationAction,
    AddPurposeAction,
)


class StateV8(State):
    purposes: dict[str, models.Purpose] = Field({})
    acts: dict[str, models.ActiveAct] = Field({})
    announcements: dict[str, models.ActiveAnnouncement] = Field({})

    @staticmethod
    def get_schema_version() -> int:
        return 8

    def get_data(self) -> dict:
        data: dict = self.model_dump()
        return data

    def get_act(self, document_type: str, procedure_type: str) -> Any | None:
        key: str = f"{document_type}-{procedure_type}"
        result: models.ActiveAct | None = self.acts.get(key)
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
                raise RuntimeError(f"Action {action.__class__.__name__} is not implemented for StateV8")

    def _handle_add_purpose_action(self, action: AddPurposeAction):
        purpose = models.Purpose(
            purpose_type=action.purpose_type.value,
            effective_date=action.get_effective_date_str(),
            work_province_id=action.work_province_id,
            work_date=action.work_date,
            work_other=action.work_other,
        )
        frbr: str = purpose.get_frbr_work()
        self.purposes[frbr] = purpose

    def _handle_add_publication_action(self, action: AddPublicationAction):
        active_act = models.ActiveAct(
            act_frbr=action.act_frbr,
            bill_frbr=action.bill_frbr,
            consolidation_purpose=action.consolidation_purpose,
            document_type=action.document_type,
            procedure_type=action.procedure_type,
            gios=action.gios,
            gebiedengroepen=action.gebiedengroepen,
            gebiedsaanwijzingen=action.gebiedsaanwijzingen,
            documents=action.documents,
            assets=action.assets,
            wid_data=action.wid_data,
            ow_state=action.ow_state,
            act_text=action.act_text,
            publication_version_uuid=action.publication_version_uuid,
        )
        key: str = f"{action.document_type}-{action.procedure_type}"
        self.acts[key] = active_act

    def _handle_add_announcement_action(self, action: AddAnnouncementAction):
        active_announcement = models.ActiveAnnouncement(
            doc_frbr=action.doc_frbr,
            about_act_frbr=action.about_act_frbr,
            about_bill_frbr=action.about_bill_frbr,
            document_type=action.document_type,
            procedure_type=action.procedure_type,
        )
        key: str = f"{action.document_type}-{action.procedure_type}"
        self.announcements[key] = active_announcement
