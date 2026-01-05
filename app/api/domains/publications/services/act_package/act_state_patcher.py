from copy import deepcopy
from typing import Dict, List, Optional, Set

import dso.models as dso_models
from dso.act_builder.services.ow.state.ow_state import OwState as DsoOwState
from dso.act_builder.builder import Builder

from app.api.domains.publications.services.state.versions import ActiveState
from app.api.domains.publications.services.state.versions.v6 import models
from app.api.domains.publications.services.state.versions.v6.actions import AddPublicationAction, AddPurposeAction
from app.api.domains.publications.types.api_input_data import ApiActInputData, Purpose
from app.core.tables.publications import PublicationTable, PublicationVersionTable


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
        gebieden: Dict[str, models.Gebied] = self._resolve_gebieden(state)
        gebiedengroepen: Dict[str, models.Gebiedengroep] = self._resolve_gebiedengroepen(state)
        gebiedsaanwijzingen: List[models.Gebiedsaanwijzing] = self._resolve_gebiedsaanwijzingen(state)
        documents: Dict[int, models.Document] = self._resolve_documents(state)
        wid_data = models.WidData(
            Known_Wid_Map=self._dso_builder.get_used_wid_map(),
            Known_Wids=self._dso_builder.get_used_wids(),
        )

        # Serialize dso_ow_state to a simple dict for result model
        dso_ow_state: DsoOwState = self._dso_builder.get_ow_state()
        dso_ow_state_json: str = dso_ow_state.model_dump_json()
        ow_state = models.OwState.model_validate_json(dso_ow_state_json)

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
            Gebieden=gebieden,
            Gebiedengroepen=gebiedengroepen,
            Gebiedsaanwijzingen=gebiedsaanwijzingen,
            Documents=documents,
            Assets=assets,
            Wid_Data=wid_data,
            Ow_State=ow_state,
            Act_Text=act_text,
            Publication_Version_UUID=str(self._publication_version.UUID),
        )
        state.handle_action(action)
        return state

    # def _resolve_gebieden(self, state: ActiveState) -> Dict[str, models.Gebied]:
    #     gebieden: Dict[str, models.Gebied] = {}

    #     # We only keep the send gebieden, as all other should have been withdrawn
    #     for dso_gebied in self._api_input_data.Publication_Data.gebieden:
    #         dso_frbr: dso_models.GioFRBR = dso_gebied["frbr"]
    #         frbr = models.Frbr(
    #             Work_Province_ID=dso_frbr.Work_Province_ID,
    #             Work_Country="",
    #             Work_Date=dso_frbr.Work_Date,
    #             Work_Other=dso_frbr.Work_Other,
    #             Expression_Language=dso_frbr.Expression_Language,
    #             Expression_Date=dso_frbr.Expression_Date,
    #             Expression_Version=dso_frbr.Expression_Version or 0,
    #         )
    #         gebied = models.Gebied(
    #             uuid=str(dso_gebied["uuid"]),
    #             identifier=dso_gebied["identfier"],
    #             gml_id=dso_gebied["gml_id"],
    #             title=dso_gebied["title"],
    #             object_id=dso_gebied["object_id"],
    #             code=dso_gebied["code"],
    #             hash=dso_gebied["hash"],
    #             geboorteregeling=dso_gebied["geboorteregeling"],
    #             achtergrond_verwijzing=dso_gebied["achtergrond_verwijzing"],
    #             achtergrond_actualiteit=dso_gebied["achtergrond_actualiteit"],
    #             frbr=frbr,
    #         )
    #         gebieden[gebied.code] = gebied

    #     return gebieden

    def _resolve_gebiedsaanwijzingen(self, state: ActiveState) -> List[models.Gebiedsaanwijzing]:
        aanwijzingen: List[models.Gebiedsaanwijzing] = []

        # We only keep the send gebiedsaanwijzingen, as all other should have been withdrawn from the ow state
        for dso_aanwijzing in self._api_input_data.Publication_Data.gebiedsaanwijzingen:
            aanwijzing = models.Gebiedsaanwijzing(
                uuid=dso_aanwijzing.uuid,
                ow_identifier=dso_aanwijzing.ow_identifier,
                aanwijzing_type=dso_aanwijzing.aanwijzing_type,
                aanwijzing_group=dso_aanwijzing.aanwijzing_group,
                title=dso_aanwijzing.title,
                target_codes=dso_aanwijzing.target_codes,
            )
            aanwijzingen.append(aanwijzing)

        return aanwijzingen

    def _resolve_gebiedengroepen(self, state: ActiveState) -> Dict[str, models.Gebiedengroep]:
        gebiedengroepen: Dict[str, models.Gebiedengroep] = {}

        # We only keep the send gebiedengroepen, as all other should have been withdrawn
        for dso_gebiedengroep in self._api_input_data.Publication_Data.gebiedengroepen:
            gebiedengroep = models.Gebiedengroep(
                uuid=str(dso_gebiedengroep["uuid"]),
                identifier=dso_gebiedengroep["identfier"],
                object_id=dso_gebiedengroep["object_id"],
                code=dso_gebiedengroep["code"],
                title=dso_gebiedengroep["title"],
                gebied_codes=dso_gebiedengroep["gebied_codes"],
            )
            gebiedengroepen[gebiedengroep.code] = gebiedengroep

        return gebiedengroepen

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
