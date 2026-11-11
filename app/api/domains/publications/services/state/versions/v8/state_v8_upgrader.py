from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

import app.api.domains.publications.services.state.versions.v7.models as models_v7
import app.api.domains.publications.services.state.versions.v8.models as models_v8
from app.api.domains.publications.services.state.state import State
from app.api.domains.publications.services.state.state_upgrader import StateUpgrader

from ..v7 import state_v7
from ..v8 import state_v8


class StateV8Upgrader(StateUpgrader):
    """
    Renamed from the old field style to the new, ex: Object_Type to object_type etc
    This version was made so we can remove the old style everywhere.

    Models that were already snake_case in v7 (Gebiedsaanwijzing, GioLocatie, OwState, ...)
    are copied over as they are.
    """

    @staticmethod
    def get_input_schema_version() -> int:
        return state_v7.StateV7.get_schema_version()

    async def upgrade(self, session: AsyncSession, environment_uuid: UUID, old_state: State) -> State:
        if old_state.get_schema_version() != state_v7.StateV7.get_schema_version():
            raise RuntimeError("Unexpected state provided")

        if not isinstance(old_state, state_v7.StateV7):
            raise RuntimeError("Unexpected state provided")

        new_state = state_v8.StateV8(
            purposes={key: self._mutate_purpose(purpose) for key, purpose in old_state.Purposes.items()},
            acts={key: self._mutate_act(act) for key, act in old_state.Acts.items()},
            announcements={
                key: self._mutate_announcement(announcement) for key, announcement in old_state.Announcements.items()
            },
        )

        return new_state

    def _mutate_purpose(self, old_purpose: models_v7.Purpose) -> models_v8.Purpose:
        return models_v8.Purpose(
            purpose_type=old_purpose.Purpose_Type,
            effective_date=old_purpose.Effective_Date,
            work_province_id=old_purpose.Work_Province_ID,
            work_date=old_purpose.Work_Date,
            work_other=old_purpose.Work_Other,
        )

    def _mutate_frbr(self, old_frbr: models_v7.Frbr) -> models_v8.Frbr:
        return models_v8.Frbr(
            work_province_id=old_frbr.Work_Province_ID,
            work_country=old_frbr.Work_Country,
            work_date=old_frbr.Work_Date,
            work_other=old_frbr.Work_Other,
            expression_language=old_frbr.Expression_Language,
            expression_date=old_frbr.Expression_Date,
            expression_version=old_frbr.Expression_Version,
        )

    def _mutate_announcement(self, old_announcement: models_v7.ActiveAnnouncement) -> models_v8.ActiveAnnouncement:
        return models_v8.ActiveAnnouncement(
            doc_frbr=self._mutate_frbr(old_announcement.Doc_Frbr),
            about_act_frbr=self._mutate_frbr(old_announcement.About_Act_Frbr),
            about_bill_frbr=self._mutate_frbr(old_announcement.About_Bill_Frbr),
            document_type=old_announcement.Document_Type,
            procedure_type=old_announcement.Procedure_Type,
        )

    def _mutate_act(self, old_act: models_v7.ActiveAct) -> models_v8.ActiveAct:
        return models_v8.ActiveAct(
            act_frbr=self._mutate_frbr(old_act.Act_Frbr),
            bill_frbr=self._mutate_frbr(old_act.Bill_Frbr),
            consolidation_purpose=self._mutate_purpose(old_act.Consolidation_Purpose),
            document_type=old_act.Document_Type,
            procedure_type=old_act.Procedure_Type,
            gios={key: self._mutate_gio(gio) for key, gio in old_act.Gios.items()},
            gebiedengroepen={
                key: self._mutate_gebiedengroep(gebiedengroep) for key, gebiedengroep in old_act.Gebiedengroepen.items()
            },
            gebiedsaanwijzingen={
                key: models_v8.Gebiedsaanwijzing.model_validate(gebiedsaanwijzing.model_dump())
                for key, gebiedsaanwijzing in old_act.Gebiedsaanwijzingen.items()
            },
            documents={key: self._mutate_document(document) for key, document in old_act.Documents.items()},
            assets={key: models_v8.Asset(id=asset.UUID) for key, asset in old_act.Assets.items()},
            wid_data=models_v8.WidData(
                known_wid_map=old_act.Wid_Data.Known_Wid_Map,
                known_wids=old_act.Wid_Data.Known_Wids,
            ),
            ow_state=models_v8.OwState.model_validate(old_act.Ow_State.model_dump()),
            act_text=old_act.Act_Text,
            publication_version_id=old_act.Publication_Version_UUID,
        )

    def _mutate_gebiedengroep(self, old_gebiedengroep: models_v7.Gebiedengroep) -> models_v8.Gebiedengroep:
        return models_v8.Gebiedengroep(
            id=old_gebiedengroep.uuid,
            code=old_gebiedengroep.code,
            title=old_gebiedengroep.title,
            source_gebieden_codes=old_gebiedengroep.source_gebieden_codes,
            gio_key=old_gebiedengroep.gio_key,
        )

    def _mutate_gio(self, old_gio: models_v7.Gio) -> models_v8.Gio:
        return models_v8.Gio(
            key=old_gio.key,
            source_codes=old_gio.source_codes,
            title=old_gio.title,
            frbr=self._mutate_frbr(old_gio.frbr),
            geboorteregeling=old_gio.geboorteregeling,
            achtergrond_verwijzing=old_gio.achtergrond_verwijzing,
            achtergrond_actualiteit=old_gio.achtergrond_actualiteit,
            locaties=[models_v8.GioLocatie.model_validate(locatie.model_dump()) for locatie in old_gio.locaties],
        )

    def _mutate_document(self, old_document: models_v7.Document) -> models_v8.Document:
        return models_v8.Document(
            id=old_document.UUID,
            code=old_document.Code,
            frbr=self._mutate_frbr(old_document.Frbr),
            filename=old_document.Filename,
            title=old_document.Title,
            owner_act=old_document.Owner_Act,
            content_type=old_document.Content_Type,
            object_id=old_document.Object_ID,
            hash=old_document.Hash,
        )
