from copy import deepcopy

from dso.announcement_builder.builder import Builder

from app.api.domains.publications.services.state.versions import ActiveState, active_actions, active_models
from app.api.domains.publications.types.api_input_data import ApiAnnouncementInputData
from app.core.tables.publications import PublicationAnnouncementTable, PublicationTable


class AnnouncementStatePatcher:
    def __init__(self, api_input_data: ApiAnnouncementInputData, dso_builder: Builder):
        self._api_input_data: ApiAnnouncementInputData = api_input_data
        self._dso_builder: Builder = dso_builder
        self._announcement: PublicationAnnouncementTable = api_input_data.announcement
        self._publication: PublicationTable = api_input_data.announcement.publication

    def apply(self, source_state: ActiveState) -> ActiveState:
        state: ActiveState = deepcopy(source_state)
        state = self._patch_announcement(state)
        return state

    def _patch_announcement(self, state: ActiveState) -> ActiveState:
        doc_frbr = active_models.Frbr(
            work_province_id=self._api_input_data.doc_frbr.work_province_id,
            work_country=self._api_input_data.doc_frbr.work_country,
            work_date=self._api_input_data.doc_frbr.work_date,
            work_other=self._api_input_data.doc_frbr.work_other,
            expression_language=self._api_input_data.doc_frbr.expression_language,
            expression_date=self._api_input_data.doc_frbr.expression_date,
            expression_version=self._api_input_data.doc_frbr.expression_version,
        )
        about_bill_frbr = active_models.Frbr(
            work_province_id=self._api_input_data.about_bill_frbr.work_province_id,
            work_country=self._api_input_data.about_bill_frbr.work_country,
            work_date=self._api_input_data.about_bill_frbr.work_date,
            work_other=self._api_input_data.about_bill_frbr.work_other,
            expression_language=self._api_input_data.about_bill_frbr.expression_language,
            expression_date=self._api_input_data.about_bill_frbr.expression_date,
            expression_version=self._api_input_data.about_bill_frbr.expression_version,
        )
        about_act_frbr = active_models.Frbr(
            work_province_id=self._api_input_data.about_act_frbr.work_province_id,
            work_country=self._api_input_data.about_act_frbr.work_country,
            work_date=self._api_input_data.about_act_frbr.work_date,
            work_other=self._api_input_data.about_act_frbr.work_other,
            expression_language=self._api_input_data.about_act_frbr.expression_language,
            expression_date=self._api_input_data.about_act_frbr.expression_date,
            expression_version=self._api_input_data.about_act_frbr.expression_version,
        )

        action = active_actions.AddAnnouncementAction(
            doc_frbr=doc_frbr,
            about_bill_frbr=about_bill_frbr,
            about_act_frbr=about_act_frbr,
            document_type=self._api_input_data.announcement.publication.document_type,
            procedure_type=self._api_input_data.announcement.publication.procedure_type,
        )
        state.handle_action(action)
        return state
