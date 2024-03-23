from typing import Optional

from app.extensions.publications.models.api_input_data import ApiInputData
from app.extensions.publications.services.state import result_models
from app.extensions.publications.services.state.patch_act_mutation import PatchActMutation
from app.extensions.publications.services.state.state import ActiveState


class ApiInputDataPatcher:
    def __init__(self, state: ActiveState):
        self._state: ActiveState = state

    def apply(self, data: ApiInputData) -> ApiInputData:
        active_act: Optional[result_models.ActiveAct] = self._state.get_act(
            data.Publication_Version.Publication.Document_Type,
            data.Publication_Version.Publication.Procedure_Type,
        )

        # If there is not act for this setup
        # Then we have nothing to do
        if active_act is None:
            return data

        if active_act.Act_Frbr.Work_Other == data.Act_Frbr.Work_Other:
            return self._handle_mutation(data, active_act)

        return self._handle_new_work(data, active_act)

    def _handle_new_work(self, data: ApiInputData, active_act: result_models.ActiveAct) -> ApiInputData:
        raise NotImplementedError("Intrekken van regeling is nog niet geimplementeerd")

    def _handle_mutation(self, data: ApiInputData, active_act: result_models.ActiveAct) -> ApiInputData:
        mutation_patcher: PatchActMutation = PatchActMutation(active_act)
        data = mutation_patcher.patch(data)
        return data
