from copy import deepcopy

from app.extensions.publications.models.api_input_data import ApiInputData, Purpose
from app.extensions.publications.services.state.actions.add_area_of_jurisdiction_action import (
    AddAreaOfJurisdictionAction,
)
from app.extensions.publications.services.state.actions.add_purpose_action import AddPurposeAction
from app.extensions.publications.services.state.actions.consolidate_werkingsgebied_action import (
    ConsolidateWerkingsgebiedAction,
)
from app.extensions.publications.services.state.state import State


class StatePatcher:
    def __init__(self, api_input_data: ApiInputData):
        self._api_input_data: ApiInputData = api_input_data

    def apply(self, source_state: State) -> State:
        state: State = deepcopy(source_state)
        state = self._patch_act(state)
        state = self._patch_consolidation_purpose(state)
        state = self._patch_werkingsgebieden(state)
        state = self._patch_area_of_jurisdiction(state)
        return state

    def _patch_act(self, state: State) -> State:
        return state

    def _patch_consolidation_purpose(self, state: State) -> State:
        purpose: Purpose = self._api_input_data.Consolidation_Purpose
        action = AddPurposeAction(
            Purpose_Type=purpose.Purpose_Type,
            Effective_Date=purpose.Effective_Date,
            Work_Province_ID=purpose.Work_Province_ID,
            Work_Date=purpose.Work_Date,
            Work_Other=purpose.Work_Other,
        )
        state.handle_action(action)
        return state

    def _patch_werkingsgebieden(self, state: State) -> State:
        for werkingsgebied in self._api_input_data.Publication_Data.werkingsgebieden:
            if not werkingsgebied["New"]:
                continue

            action = ConsolidateWerkingsgebiedAction(
                UUID=werkingsgebied["UUID"],
                Object_ID=werkingsgebied["Object_ID"],
                Work="",  # @todo: jordy werkingsgebied["Work"],
                Expression_Version="",  # @todo: jordy werkingsgebied["Expression_Version"],
                Act_Frbr=self._api_input_data.Act_Frbr,
                Consolidation_Purpose=self._api_input_data.Consolidation_Purpose,
            )
            state.handle_action(action)

        return state

    def _patch_area_of_jurisdiction(self, state: State) -> State:
        aoj: dict = self._api_input_data.Publication_Data.area_of_jurisdiction
        if not aoj["New"]:
            return state

        action = AddAreaOfJurisdictionAction(
            UUID=aoj["UUID"],
            Administrative_Borders_ID=aoj["Administrative_Borders_ID"],
            Act_Frbr=self._api_input_data.Act_Frbr,
        )
        state.handle_action(action)
        return state
