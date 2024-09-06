from typing import Optional

from app.extensions.publications.enums import ProcedureType
from app.extensions.publications.models.api_input_data import ApiActInputData
from app.extensions.publications.services.state.patch_act_mutation import PatchActMutation
from app.extensions.publications.services.state.versions import ActiveState
from app.extensions.publications.services.state.versions.v2.models import ActiveAct


class ApiActInputDataPatcher:
    def __init__(self, state: ActiveState):
        self._state: ActiveState = state

    def apply(self, data: ApiActInputData) -> ApiActInputData:
        # @note:
        # For now we can only mutate on a Final ("Definitief")
        # So for example:
        # - A Draft is applied on top of the latest Final
        # - A Final is applied on top of the latest Final
        #
        # In the future, it might be that you want to make a change on your draft.
        # So for example:
        # - You create a Draft on top of the latest Final
        # - You want to make minor changes on your Draft -> Get the latest Draft (the source Draft)
        # We do no support this flow anyware in our system yet,
        # Therefor I did not take the time to fix it here
        active_act: Optional[ActiveAct] = self._state.get_act(
            data.Publication_Version.Publication.Document_Type,
            ProcedureType.FINAL,
        )

        # If there is not act for this setup
        # Then we have nothing to do
        if active_act is None:
            return data

        if active_act.Act_Frbr.Work_Other == data.Act_Frbr.Work_Other:
            return self._handle_mutation(data, active_act)

        return self._handle_new_work(data, active_act)

    def _handle_new_work(self, data: ApiActInputData, active_act: ActiveAct) -> ApiActInputData:
        raise NotImplementedError("Intrekken van regeling is nog niet geimplementeerd")

    def _handle_mutation(self, data: ApiActInputData, active_act: ActiveAct) -> ApiActInputData:
        mutation_patcher: PatchActMutation = PatchActMutation(active_act)
        data = mutation_patcher.patch(data)
        return data
