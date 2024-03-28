from copy import deepcopy

from dso.announcement_builder.builder import Builder

from app.extensions.publications.models.api_input_data import ApiAnnouncementInputData
from app.extensions.publications.services.state.state import ActiveState
from app.extensions.publications.tables.tables import PublicationAnnouncementTable, PublicationTable


class AnnouncementStatePatcher:
    def __init__(self, api_input_data: ApiAnnouncementInputData, dso_builder: Builder):
        self._api_input_data: ApiAnnouncementInputData = api_input_data
        self._dso_builder: Builder = dso_builder
        self._announcement: PublicationAnnouncementTable = api_input_data.Announcement
        self._publication: PublicationTable = api_input_data.Announcement.Publication

    def apply(self, source_state: ActiveState) -> ActiveState:
        state: ActiveState = deepcopy(source_state)
        # @todo: store state
        return state
