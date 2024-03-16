from copy import deepcopy

from app.extensions.publications.models.api_input_data import ApiInputData
from app.extensions.publications.services.state.actions.consolidate_area_of_jurisdiction_action import (
    ConsolidateAreaOfJurisdictionAction,
)
from app.extensions.publications.services.state.actions.consolidate_werkingsgebied_action import (
    ConsolidateWerkingsgebiedAction,
)
from app.extensions.publications.services.state.state import State


class StateChanger:
    def __init__(self, api_input_data: ApiInputData):
        self._api_input_data: ApiInputData = api_input_data

    def apply(self, source_state: State) -> State:
        state: State = deepcopy(source_state)
        state = self._patch_werkingsgebieden(state)
        state = self._patch_area_of_jurisdiction(state)
        return state

    def _patch_act(self, state: State) -> State:
        aoj: dict = self._api_input_data.Publication_Data.area_of_jurisdiction
        if not aoj["New"]:
            return state

        action = ConsolidateAreaOfJurisdictionAction(
            UUID=aoj["UUID"],
            Administrative_Borders_ID=aoj["Administrative_Borders_ID"],
            Act_Frbr=self._api_input_data.Act_Frbr,
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
                Work=werkingsgebied["Work"],
                Expression_Version=werkingsgebied["Expression_Version"],
                Act_Frbr=self._api_input_data.Act_Frbr,
            )
            state.handle_action(action)

        return state

    def _patch_area_of_jurisdiction(self, state: State) -> State:
        aoj: dict = self._api_input_data.Publication_Data.area_of_jurisdiction
        if not aoj["New"]:
            return state

        action = ConsolidateAreaOfJurisdictionAction(
            UUID=aoj["UUID"],
            Administrative_Borders_ID=aoj["Administrative_Borders_ID"],
            Act_Frbr=self._api_input_data.Act_Frbr,
        )
        state.handle_action(action)
        return state
