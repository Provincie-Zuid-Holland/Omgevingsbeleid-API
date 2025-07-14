from copy import deepcopy
from typing import Dict, List, Optional, Set

import dso.models as dso_models
from dso.act_builder.builder import Builder

from app.api.domains.publications.services.state.versions import ActiveState
from app.api.domains.publications.services.state.versions.v4 import models
from app.api.domains.publications.services.state.versions.v4.actions import AddPublicationAction, AddPurposeAction
from app.api.domains.publications.types.api_input_data import ApiActInputData, Purpose
from app.core.tables.publications import PublicationTable, PublicationVersionTable
from app.core.utils.utils import serialize_data


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
        documents: Dict[int, models.Document] = self._resolve_documents(state)
        wid_data = models.WidData(
            Known_Wid_Map=self._dso_builder.get_used_wid_map(),
            Known_Wids=self._dso_builder.get_used_wids(),
        )

        # Serialize dso_ow_state to a simple dict for result model
        dso_ow_state: dso_models.OwData = self._dso_builder.get_ow_object_state()
        dso_ow_state_dict: dict = dso_ow_state.model_dump()
        dso_ow_state_dict_serialized: dict = serialize_data(dso_ow_state_dict)
        ow_data = models.OwData.model_validate(
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

        used_asset_uuids: Set[str] = self._dso_builder.get_used_asset_uuids()
        assets: Dict[str, models.Asset] = {uuidx: models.Asset(UUID=uuidx) for uuidx in used_asset_uuids}

        action = AddPublicationAction(
            Act_Frbr=act_frbr,
            Bill_Frbr=bill_frbr,
            Consolidation_Purpose=purpose,
            Document_Type=self._api_input_data.Publication_Version.Publication.Document_Type,
            Procedure_Type=self._api_input_data.Publication_Version.Publication.Procedure_Type,
            Werkingsgebieden=werkingsgebieden,
            Documents=documents,
            Assets=assets,
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
            locations: List[models.Location] = [
                models.Location(
                    UUID=str(l["UUID"]),
                    Identifier=l["Identifier"],
                    Gml_ID=l["Gml_ID"],
                    Group_ID=l["Group_ID"],
                    Title=l["Title"],
                )
                for l in dso_werkingsgebied["Locaties"]
            ]
            werkingsgebied = models.Werkingsgebied(
                UUID=str(dso_werkingsgebied["UUID"]),
                Identifier=str(dso_werkingsgebied["Identifier"]),
                Hash=dso_werkingsgebied["Hash"],
                Object_ID=dso_werkingsgebied["Object_ID"],
                Title=dso_werkingsgebied["Title"],
                Owner_Act=dso_werkingsgebied["Geboorteregeling"],
                Frbr=frbr,
                Locations=locations,
            )
            werkingsgebieden[werkingsgebied.Object_ID] = werkingsgebied

        return werkingsgebieden

    def _resolve_documents(self, state: ActiveState) -> Dict[int, models.Document]:
        documents: Dict[int, models.Document] = {}

        # We only keep the send documents, as all other should have been withdrawn
        for dso_document in self._api_input_data.Publication_Data.documents:
            dso_frbr: dso_models.GioFRBR = dso_document["Frbr"]
            frbr = models.Frbr(
                Work_Province_ID=dso_frbr.Work_Province_ID,
                Work_Country="",
                Work_Date=dso_frbr.Work_Date,
                Work_Other=dso_frbr.Work_Other,
                Expression_Language=dso_frbr.Expression_Language,
                Expression_Date=dso_frbr.Expression_Date,
                Expression_Version=dso_frbr.Expression_Version or 0,
            )
            document = models.Document(
                UUID=str(dso_document["UUID"]),
                Code=str(dso_document["Code"]),
                Frbr=frbr,
                Filename=dso_document["Filename"],
                Title=dso_document["Title"],
                Owner_Act=dso_document["Geboorteregeling"],
                Content_Type=dso_document["Content_Type"],
                Object_ID=dso_document["Object_ID"],
                Hash=dso_document["Hash"],
            )
            documents[document.Object_ID] = document

        return documents

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
