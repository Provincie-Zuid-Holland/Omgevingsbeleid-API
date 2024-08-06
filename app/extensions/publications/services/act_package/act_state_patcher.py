from copy import deepcopy
from typing import Dict, Optional

import dso.models as dso_models
from dso.act_builder.builder import Builder

from app.extensions.publications.models.api_input_data import ApiActInputData, Purpose
from app.extensions.publications.services.state import result_models
from app.extensions.publications.services.state.actions.add_publication_action import AddPublicationAction
from app.extensions.publications.services.state.actions.add_purpose_action import AddPurposeAction
from app.extensions.publications.services.state.state import ActiveState
from app.extensions.publications.tables.tables import PublicationTable


class ActStatePatcher:
    def __init__(self, api_input_data: ApiActInputData, dso_builder: Builder):
        self._api_input_data: ApiActInputData = api_input_data
        self._dso_builder: Builder = dso_builder
        self._publication: PublicationTable = api_input_data.Publication_Version.Publication

    def apply(self, source_state: ActiveState) -> ActiveState:
        state: ActiveState = deepcopy(source_state)
        state = self._patch_publication(state)
        state = self._patch_consolidation_purpose(state)
        return state

    def _patch_publication(self, state: ActiveState) -> ActiveState:
        werkingsgebieden: Dict[int, result_models.Werkingsgebied] = self._resolve_werkingsgebieden(state)
        wid_data = result_models.WidData(
            Known_Wid_Map=self._dso_builder.get_used_wid_map(),
            Known_Wids=self._dso_builder.get_used_wids(),
        )

        # Serialize dso_ow_state to a simple dict for result model
        dso_ow_state: dso_models.OwData = self._dso_builder.get_ow_object_state()
        ow_data = result_models.OwData.parse_raw(dso_ow_state.json())

        input_purpose = self._api_input_data.Consolidation_Purpose
        effective_date: Optional[str] = None
        if input_purpose.Effective_Date is not None:
            effective_date = input_purpose.Effective_Date.strftime("%Y-%m-%d")
        purpose = result_models.Purpose(
            Purpose_Type=input_purpose.Purpose_Type.value,
            Effective_Date=effective_date,
            Work_Province_ID=input_purpose.Work_Province_ID,
            Work_Date=input_purpose.Work_Date,
            Work_Other=input_purpose.Work_Other,
        )

        act_frbr = result_models.Frbr(
            Work_Province_ID=self._api_input_data.Act_Frbr.Work_Province_ID,
            Work_Country=self._api_input_data.Act_Frbr.Work_Country,
            Work_Date=self._api_input_data.Act_Frbr.Work_Date,
            Work_Other=self._api_input_data.Act_Frbr.Work_Other,
            Expression_Language=self._api_input_data.Act_Frbr.Expression_Language,
            Expression_Date=self._api_input_data.Act_Frbr.Expression_Date,
            Expression_Version=self._api_input_data.Act_Frbr.Expression_Version,
        )
        bill_frbr = result_models.Frbr(
            Work_Province_ID=self._api_input_data.Bill_Frbr.Work_Province_ID,
            Work_Country=self._api_input_data.Bill_Frbr.Work_Country,
            Work_Date=self._api_input_data.Bill_Frbr.Work_Date,
            Work_Other=self._api_input_data.Bill_Frbr.Work_Other,
            Expression_Language=self._api_input_data.Bill_Frbr.Expression_Language,
            Expression_Date=self._api_input_data.Bill_Frbr.Expression_Date,
            Expression_Version=self._api_input_data.Bill_Frbr.Expression_Version,
        )

        act_text: Optional[str] = self._dso_builder.get_regeling_vrijetekst()
        if act_text is None:
            raise RuntimeError("Regeling vrijetekst bestaat niet")

        action = AddPublicationAction(
            Act_Frbr=act_frbr,
            Bill_Frbr=bill_frbr,
            Consolidation_Purpose=purpose,
            Document_Type=self._api_input_data.Publication_Version.Publication.Document_Type,
            Procedure_Type=self._api_input_data.Publication_Version.Publication.Procedure_Type,
            Werkingsgebieden=werkingsgebieden,
            Wid_Data=wid_data,
            Ow_Data=ow_data,
            Act_Text=act_text,
        )
        state.handle_action(action)
        return state

    def _resolve_werkingsgebieden(self, state: ActiveState) -> Dict[int, result_models.Werkingsgebied]:
        existing_act: Optional[result_models.ActiveAct] = state.get_act(
            self._publication.Document_Type,
            self._publication.Procedure_Type,
        )
        werkingsgebieden: Dict[int, result_models.Werkingsgebied] = {}
        if existing_act is not None:
            werkingsgebieden = existing_act.Werkingsgebieden

        # @note: We have not implemented terminating werkingsgebieden yet
        # So we can just merge the existing list with the new list
        # Overwriting werkingsgebieden with the same Object_ID
        for dso_werkingsgebied in self._api_input_data.Publication_Data.werkingsgebieden:
            dso_frbr: dso_models.GioFRBR = dso_werkingsgebied["Frbr"]
            frbr = result_models.Frbr(
                Work_Province_ID=dso_frbr.Work_Province_ID,
                Work_Country="",
                Work_Date=dso_frbr.Work_Date,
                Work_Other=dso_frbr.Work_Other,
                Expression_Language=dso_frbr.Expression_Language,
                Expression_Date=dso_frbr.Expression_Date,
                Expression_Version=dso_frbr.Expression_Version,
            )
            werkingsgebied = result_models.Werkingsgebied(
                UUID=str(dso_werkingsgebied["UUID"]),
                Object_ID=dso_werkingsgebied["Object_ID"],
                Owner_Act=dso_werkingsgebied["Geboorteregeling"],
                Frbr=frbr,
            )
            werkingsgebieden[werkingsgebied.Object_ID] = werkingsgebied

        return werkingsgebieden

    def _patch_consolidation_purpose(self, state: ActiveState) -> ActiveState:
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
