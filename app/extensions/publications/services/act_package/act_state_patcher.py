from copy import deepcopy
from typing import Dict, Optional

import dso.models as dso_models
from dso.act_builder.builder import Builder

from app.core.utils.utils import serialize_data
from app.extensions.publications.models.api_input_data import ApiActInputData, Purpose
from app.extensions.publications.services.state.versions import ActiveState
from app.extensions.publications.services.state.versions.v2 import models
from app.extensions.publications.services.state.versions.v2.actions import AddPublicationAction, AddPurposeAction
from app.extensions.publications.tables.tables import PublicationTable, PublicationVersionTable


class ActStatePatcher:
    def __init__(self, api_input_data: ApiActInputData, dso_builder: Builder):
        self._api_input_data: ApiActInputData = api_input_data
        self._dso_builder: Builder = dso_builder
        self._publication_version: PublicationVersionTable = api_input_data.Publication_Version
        self._publication: PublicationTable = api_input_data.Publication_Version.Publication

    def apply(self, source_state: ActiveState) -> ActiveState:
        state: ActiveState = deepcopy(source_state)
        state = self._patch_publication(state)
        state = self._patch_consolidation_purpose(state)
        return state

    def _patch_publication(self, state: ActiveState) -> ActiveState:
        werkingsgebieden: Dict[int, models.Werkingsgebied] = self._resolve_werkingsgebieden(state)
        wid_data = models.WidData(
            Known_Wid_Map=self._dso_builder.get_used_wid_map(),
            Known_Wids=self._dso_builder.get_used_wids(),
        )

        # Serialize dso_ow_state to a simple dict for result model
        dso_ow_state: dso_models.OwData = self._dso_builder.get_ow_object_state()
        dso_ow_state_dict: dict = dso_ow_state.dict()
        dso_ow_state_dict_serialized: dict = serialize_data(dso_ow_state_dict)
        ow_data = models.OwData.parse_obj(
            {
                "Ow_Objects": dso_ow_state_dict_serialized["ow_objects"],
                "Terminated_Ow_Ids": dso_ow_state_dict_serialized["terminated_ow_ids"],
            }
        )

        input_purpose = self._api_input_data.Consolidation_Purpose
        effective_date: Optional[str] = None
        if input_purpose.Effective_Date is not None:
            effective_date = input_purpose.Effective_Date.strftime("%Y-%m-%d")
        purpose = models.Purpose(
            Purpose_Type=input_purpose.Purpose_Type.value,
            Effective_Date=effective_date,
            Work_Province_ID=input_purpose.Work_Province_ID,
            Work_Date=input_purpose.Work_Date,
            Work_Other=input_purpose.Work_Other,
        )

        act_frbr = models.Frbr(
            Work_Province_ID=self._api_input_data.Act_Frbr.Work_Province_ID,
            Work_Country=self._api_input_data.Act_Frbr.Work_Country,
            Work_Date=self._api_input_data.Act_Frbr.Work_Date,
            Work_Other=self._api_input_data.Act_Frbr.Work_Other,
            Expression_Language=self._api_input_data.Act_Frbr.Expression_Language,
            Expression_Date=self._api_input_data.Act_Frbr.Expression_Date,
            Expression_Version=self._api_input_data.Act_Frbr.Expression_Version,
        )
        bill_frbr = models.Frbr(
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
            Publication_Version_UUID=str(self._publication_version.UUID),
        )
        state.handle_action(action)
        return state

    def _resolve_werkingsgebieden(self, state: ActiveState) -> Dict[int, models.Werkingsgebied]:
        werkingsgebieden: Dict[int, models.Werkingsgebied] = {}

        # We only keep the send werkingsgebieden, as all other should have been withdrawn
        for dso_werkingsgebied in self._api_input_data.Publication_Data.werkingsgebieden:
            dso_frbr: dso_models.GioFRBR = dso_werkingsgebied["Frbr"]
            frbr = models.Frbr(
                Work_Province_ID=dso_frbr.Work_Province_ID,
                Work_Country="",
                Work_Date=dso_frbr.Work_Date,
                Work_Other=dso_frbr.Work_Other,
                Expression_Language=dso_frbr.Expression_Language,
                Expression_Date=dso_frbr.Expression_Date,
                Expression_Version=dso_frbr.Expression_Version or 0,
            )
            werkingsgebied = models.Werkingsgebied(
                UUID=str(dso_werkingsgebied["UUID"]),
                Hash=dso_werkingsgebied["Hash"],
                Object_ID=dso_werkingsgebied["Object_ID"],
                Title=dso_werkingsgebied["Title"],
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
