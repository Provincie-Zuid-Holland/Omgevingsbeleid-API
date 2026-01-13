from typing import Dict, List, Optional, Set
from uuid import UUID

from sqlalchemy.orm import Session

from app.api.domains.publications.services.assets.publication_asset_provider import PublicationAssetProvider
from app.api.domains.publications.services.state.versions.v6 import models
from app.api.domains.publications.types.api_input_data import ActFrbr, ActMutation, ApiActInputData, PublicationGio
import dso.models as dso_models


class PatchActMutation:
    def __init__(self, asset_provider: PublicationAssetProvider, active_act: models.ActiveAct):
        self._asset_provider: PublicationAssetProvider = asset_provider
        self._active_act: models.ActiveAct = active_act

    def patch(self, session: Session, data: ApiActInputData) -> ApiActInputData:
        data = self._patch_gios(data)
        data = self._patch_documents(data)
        data = self._patch_assets(session, data)
        data = self._patch_act_mutation(data)
        data = self._patch_ow_state(data)
        return data

    def _patch_gios(self, data: ApiActInputData) -> ApiActInputData:
        state_gios: Dict[str, models.Gio] = self._active_act.Gios

        gios: Dict[str, PublicationGio] = data.Publication_Data.gios
        for index, gio in gios.items():
            existing_gio: Optional[models.Gio] = state_gios.get(gio.key())
            if existing_gio is None:
                continue

            # If gebied is the same, then we use the state data
            # and define the gebied as not new
            if self._gio_data_is_same(existing_gio, gio):
                gio.new = False
                gio.geboorteregeling = existing_gio.geboorteregeling
                gio.achtergrond_verwijzing = existing_gio.achtergrond_verwijzing
                gio.achtergrond_actualiteit = existing_gio.achtergrond_actualiteit

                # Keep the same FRBR
                gio.frbr = dso_models.GioFRBR.model_validate(existing_gio.frbr)
            else:
                # If the hash are different that we will publish this as a new version
                gio.new = True
                gio.geboorteregeling = existing_gio.geboorteregeling
                # Keep the same FRBR Work, but new expression
                gio.frbr.Work_Province_ID = existing_gio.frbr.Work_Province_ID
                gio.frbr.Work_Date = existing_gio.frbr.Work_Date
                gio.frbr.Work_Other = existing_gio.frbr.Work_Other
                gio.frbr.Expression_Version = existing_gio.frbr.Expression_Version + 1

            gios[index] = gio

        data.Publication_Data.gios = gios

        return data

    def _gio_data_is_same(self, existing: models.Gio, current: PublicationGio) -> bool:
        if existing.source_codes != current.source_codes:
            return False

        existing_hashes: Set[str] = {location.source_hash for location in existing.locaties}
        current_hashes: Set[str] = {location.source_hash for location in current.locaties}

        return existing_hashes == current_hashes

    def _patch_documents(self, data: ApiActInputData) -> ApiActInputData:
        state_documents: Dict[int, models.Document] = self._active_act.Documents

        documents: List[dict] = data.Publication_Data.documents
        for index, document in enumerate(documents):
            object_id: int = document["Object_ID"]
            existing_document: Optional[models.Document] = state_documents.get(object_id)
            if existing_document is None:
                continue

            # If the Hash are the same, then we use the state data
            # and define the document as not new
            if str(document["Hash"]) == existing_document.Hash:
                documents[index]["New"] = False
                documents[index]["UUID"] = existing_document.UUID
                documents[index]["Geboorteregeling"] = existing_document.Owner_Act
                # Keep the same FRBR
                documents[index]["Frbr"].Work_Province_ID = existing_document.Frbr.Work_Province_ID
                documents[index]["Frbr"].Work_Date = existing_document.Frbr.Work_Date
                documents[index]["Frbr"].Work_Other = existing_document.Frbr.Work_Other
                documents[index]["Frbr"].Expression_Language = existing_document.Frbr.Expression_Language
                documents[index]["Frbr"].Expression_Date = existing_document.Frbr.Expression_Date
                documents[index]["Frbr"].Expression_Version = existing_document.Frbr.Expression_Version
            else:
                # If the hash are different that we will publish this as a new version
                documents[index]["New"] = True
                documents[index]["Geboorteregeling"] = existing_document.Owner_Act
                # Keep the same FRBR Work, but new expression
                documents[index]["Frbr"].Work_Province_ID = existing_document.Frbr.Work_Province_ID
                documents[index]["Frbr"].Work_Date = existing_document.Frbr.Work_Date
                documents[index]["Frbr"].Work_Other = existing_document.Frbr.Work_Other
                documents[index]["Frbr"].Expression_Version = existing_document.Frbr.Expression_Version + 1

        data.Publication_Data.documents = documents

        return data

    def _gebiedengroep_is_same(self, existing: models.Gebiedengroep, gebiedengroep: dict) -> bool:
        return gebiedengroep["code"] == existing.code

    def _patch_assets(self, session: Session, data: ApiActInputData) -> ApiActInputData:
        state_assets: Dict[str, models.Asset] = self._active_act.Assets

        fetched_assets_uuids: Set[str] = set([a["UUID"] for a in data.Publication_Data.assets])
        additional_asset_uuids_str: Set[str] = set(
            [sa.UUID for _, sa in state_assets.items() if sa.UUID not in fetched_assets_uuids]
        )
        additional_asset_uuids: List[UUID] = [UUID(uuid_str) for uuid_str in additional_asset_uuids_str]
        additional_assets: List[dict] = self._asset_provider.get_assets_by_uuids(session, additional_asset_uuids)

        data.Publication_Data.assets = data.Publication_Data.assets + additional_assets

        return data

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
            Removed_Gios=self._get_removed_gios(data.Publication_Data.gios),
        )
        return data

    def _get_removed_gios(self, input_gios: Dict[str, PublicationGio]) -> List[dict]:
        state_gios: Dict[str, models.Gio] = self._active_act.Gios
        removed_gios: List[dict] = []

        for state_gio_key, state_gio in state_gios.items():
            if state_gio_key in input_gios:
                continue

            removed_gio: dict = {
                "source_codes": state_gio.source_codes,
                "geboorteregeling": state_gio.geboorteregeling,
                "titel": state_gio.title,
                "frbr": state_gio.frbr.model_dump(),
            }
            removed_gios.append(removed_gio)

        return removed_gios

    def _patch_ow_state(self, data: ApiActInputData) -> ApiActInputData:
        data.Ow_State = self._active_act.Ow_State.model_dump_json()
        return data
