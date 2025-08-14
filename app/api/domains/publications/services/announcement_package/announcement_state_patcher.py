from copy import deepcopy

from dso.announcement_builder.builder import Builder

from app.api.domains.publications.services.state.versions import ActiveState
from app.api.domains.publications.services.state.versions.v5 import models
from app.api.domains.publications.services.state.versions.v5.actions import AddAnnouncementAction
from app.api.domains.publications.types.api_input_data import ApiAnnouncementInputData
from app.core.tables.publications import PublicationAnnouncementTable, PublicationTable


class AnnouncementStatePatcher:
    def __init__(self, api_input_data: ApiAnnouncementInputData, dso_builder: Builder):
        self._api_input_data: ApiAnnouncementInputData = api_input_data
        self._dso_builder: Builder = dso_builder
        self._announcement: PublicationAnnouncementTable = api_input_data.Announcement
        self._publication: PublicationTable = api_input_data.Announcement.Publication

    def apply(self, source_state: ActiveState) -> ActiveState:
        state: ActiveState = deepcopy(source_state)
        state = self._patch_announcement(state)
        return state

    def _patch_announcement(self, state: ActiveState) -> ActiveState:
        doc_frbr = models.Frbr(
            Work_Province_ID=self._api_input_data.Doc_Frbr.Work_Province_ID,
            Work_Country=self._api_input_data.Doc_Frbr.Work_Country,
            Work_Date=self._api_input_data.Doc_Frbr.Work_Date,
            Work_Other=self._api_input_data.Doc_Frbr.Work_Other,
            Expression_Language=self._api_input_data.Doc_Frbr.Expression_Language,
            Expression_Date=self._api_input_data.Doc_Frbr.Expression_Date,
            Expression_Version=self._api_input_data.Doc_Frbr.Expression_Version,
        )
        about_bill_frbr = models.Frbr(
            Work_Province_ID=self._api_input_data.About_Bill_Frbr.Work_Province_ID,
            Work_Country=self._api_input_data.About_Bill_Frbr.Work_Country,
            Work_Date=self._api_input_data.About_Bill_Frbr.Work_Date,
            Work_Other=self._api_input_data.About_Bill_Frbr.Work_Other,
            Expression_Language=self._api_input_data.About_Bill_Frbr.Expression_Language,
            Expression_Date=self._api_input_data.About_Bill_Frbr.Expression_Date,
            Expression_Version=self._api_input_data.About_Bill_Frbr.Expression_Version,
        )
        about_act_frbr = models.Frbr(
            Work_Province_ID=self._api_input_data.About_Act_Frbr.Work_Province_ID,
            Work_Country=self._api_input_data.About_Act_Frbr.Work_Country,
            Work_Date=self._api_input_data.About_Act_Frbr.Work_Date,
            Work_Other=self._api_input_data.About_Act_Frbr.Work_Other,
            Expression_Language=self._api_input_data.About_Act_Frbr.Expression_Language,
            Expression_Date=self._api_input_data.About_Act_Frbr.Expression_Date,
            Expression_Version=self._api_input_data.About_Act_Frbr.Expression_Version,
        )

        action = AddAnnouncementAction(
            Doc_Frbr=doc_frbr,
            About_Bill_Frbr=about_bill_frbr,
            About_Act_Frbr=about_act_frbr,
            Document_Type=self._api_input_data.Announcement.Publication.Document_Type,
            Procedure_Type=self._api_input_data.Announcement.Publication.Procedure_Type,
        )
        state.handle_action(action)
        return state
