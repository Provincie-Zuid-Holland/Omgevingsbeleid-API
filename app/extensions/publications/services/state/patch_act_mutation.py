from typing import Dict, List, Optional, Set

from app.extensions.publications.models.api_input_data import ActFrbr, ActMutation, ApiActInputData, OwData
from app.extensions.publications.services.state.versions.v2 import models


class PatchActMutation:
    def __init__(self, active_act: models.ActiveAct):
        self._active_act: models.ActiveAct = active_act

    def patch(self, data: ApiActInputData) -> ApiActInputData:
        data = self._patch_werkingsgebieden(data)
        data = self._patch_act_mutation(data)
        data = self._patch_ow_data(data)
        return data

    def _patch_werkingsgebieden(self, data: ApiActInputData) -> ApiActInputData:
        state_werkingsgebieden: Dict[int, models.Werkingsgebied] = self._active_act.Werkingsgebieden

        werkingsgebieden: List[dict] = data.Publication_Data.werkingsgebieden
        for index, werkingsgebied in enumerate(werkingsgebieden):
            object_id: int = werkingsgebied["Object_ID"]
            existing_werkingsgebied: Optional[models.Werkingsgebied] = state_werkingsgebieden.get(object_id)
            if existing_werkingsgebied is None:
                continue

            # If the Hash are the same, then we use the state data
            # and define the werkingsgebied as not new
            if str(werkingsgebied["Hash"]) == existing_werkingsgebied.Hash:
                werkingsgebieden[index]["New"] = False
                werkingsgebieden[index]["UUID"] = existing_werkingsgebied.UUID
                werkingsgebieden[index]["Identifier"] = existing_werkingsgebied.Identifier
                werkingsgebieden[index]["Frbr"].Expression_Date = existing_werkingsgebied.Frbr.Expression_Date
                werkingsgebieden[index]["Frbr"].Expression_Version = existing_werkingsgebied.Frbr.Expression_Version
            else:
                # If the hash are different that we will publish this as a new version
                werkingsgebieden[index]["New"] = True
                werkingsgebieden[index]["Frbr"].Expression_Version = existing_werkingsgebied.Frbr.Expression_Version + 1

        data.Publication_Data.werkingsgebieden = werkingsgebieden

        return data

    def _get_removed_werkingsgebieden(self, data: ApiActInputData) -> List[dict]:
        used_werkingsgebieden_ids: Set[int] = set([w["Object_ID"] for w in data.Publication_Data.werkingsgebieden])

        state_werkingsgebieden: Dict[int, models.Werkingsgebied] = self._active_act.Werkingsgebieden
        removed_werkingsgebiedenen: List[dict] = []

        for werkingsgebied_id, state_werkingsgebied in state_werkingsgebieden.items():
            if werkingsgebied_id in used_werkingsgebieden_ids:
                continue

            removed_werkingsgebied: dict = {
                "UUID": state_werkingsgebied.UUID,
                "Code": f"werkingsgebied-{state_werkingsgebied.Object_ID}",
                "Object_ID": state_werkingsgebied.Object_ID,
                "Owner_Act": state_werkingsgebied.Owner_Act,
                "Title": state_werkingsgebied.Title,
                "Frbr": state_werkingsgebied.Frbr.dict(),
            }
            removed_werkingsgebiedenen.append(removed_werkingsgebied)

        return removed_werkingsgebiedenen

    def _patch_act_mutation(self, data: ApiActInputData) -> ApiActInputData:
        consolidated_frbr: ActFrbr = ActFrbr(
            Act_ID=0,
            Work_Province_ID=self._active_act.Act_Frbr.Work_Province_ID,
            Work_Country=self._active_act.Act_Frbr.Work_Country,
            Work_Date=self._active_act.Act_Frbr.Work_Date,
            Work_Other=self._active_act.Act_Frbr.Work_Other,
            Expression_Language=self._active_act.Act_Frbr.Expression_Language,
            Expression_Date=self._active_act.Act_Frbr.Expression_Date,
            Expression_Version=self._active_act.Act_Frbr.Expression_Version,
        )
        data.Act_Mutation = ActMutation(
            Consolidated_Act_Frbr=consolidated_frbr,
            Consolidated_Act_Text=self._active_act.Act_Text,
            Known_Wid_Map=self._active_act.Wid_Data.Known_Wid_Map,
            Known_Wids=self._active_act.Wid_Data.Known_Wids,
            Removed_Werkingsgebieden=self._get_removed_werkingsgebieden(data),
        )
        return data

    def _patch_ow_data(self, data: ApiActInputData) -> ApiActInputData:
        data.Ow_Data = OwData(
            ow_objects=self._active_act.Ow_Data.Ow_Objects,
            terminated_ow_ids=self._active_act.Ow_Data.Terminated_Ow_Ids,
        )
        return data
