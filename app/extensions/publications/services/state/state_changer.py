from copy import deepcopy

from app.extensions.publications.models.api_input_data import ApiInputData
from app.extensions.publications.services.state.actions.add_werkingsgebied import AddWerkingsgebiedAction
from app.extensions.publications.services.state.state import State


class StateChanger:
    def __init__(self, api_input_data: ApiInputData):
        self._api_input_data: ApiInputData = api_input_data

    def apply(self, source_state: State) -> State:
        state: State = deepcopy(source_state)
        state = self._patch_werkingsgebieden(state)
        return state

    def _patch_werkingsgebieden(self, state: State) -> State:
        for werkingsgebied in self._api_input_data.Publication_Data.werkingsgebieden:
            if not werkingsgebied["New"]:
                continue

            action = AddWerkingsgebiedAction(
                UUID=werkingsgebied["UUID"],
                Object_ID=werkingsgebied["Object_ID"],
                Work=werkingsgebied["Work"],
                Expression_Version=werkingsgebied["Expression_Version"],
                Act_Frbr=self._api_input_data.Act_Frbr,
            )
            state.handle_action(action)

        return state
