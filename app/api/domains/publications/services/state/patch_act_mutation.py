from typing import Dict, List, Optional, Set
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.publications.services.assets.publication_asset_provider import PublicationAssetProvider
from app.api.domains.publications.services.state.versions.v7 import models
from app.api.domains.publications.types.api_input_data import ActFrbr, ActMutation, ApiActInputData, PublicationGio
import dso.models as dso_models


# used_by: owner codes (gebiedengroep / gebiedsaanwijzing) that referenced
# this state gio in the previous publication. A state gio is claimed at most
# once, by the first new gio that reuses its lineage.
class StateGioEntry(BaseModel):
    used_by: Set[str]
    state_gio: models.Gio
    claimed: bool = False


class StateGioPool:
    """
    Tracks the gios of the previous publication so a new gio can reuse their
    FRBR lineage instead of minting a brand new gio.

    The stable identity across publications is the owner code
    (gebiedengroep / gebiedsaanwijzing), not the gio key (which only reflects
    whichever owner produced the geometry first). So we match by owner: a new
    gio inherits the state gio that one of its owners referenced last time.

    Upstream deduplication already collapsed "reuse a gio more than once"
    into a single api gio shared by multiple owners, so every state gio is
    claimable exactly once. A state gio that nobody claims is no longer used
    and must be withdrawn.
    """

    def __init__(self, active_act: models.ActiveAct):
        self._entries: List[StateGioEntry] = []
        for gio_key, state_gio in active_act.Gios.items():
            used_by: Set[str] = set()
            for groep in active_act.Gebiedengroepen.values():
                if groep.gio_key == gio_key:
                    used_by.add(groep.code)
            for aanwijzing in active_act.Gebiedsaanwijzingen.values():
                if aanwijzing.gio_key == gio_key:
                    used_by.add(aanwijzing.code)

            self._entries.append(
                StateGioEntry(
                    used_by=used_by,
                    state_gio=state_gio,
                )
            )

    def claim(self, new_gio: PublicationGio, owner_codes: List[str]) -> PublicationGio:
        """
        `owner_codes` must be ordered by priority: the first owner whose
        state gio is still unclaimed wins. Without a usable state gio
        `new_gio` is returned unchanged, keeping its own new FRBR.
        """
        for owner_code in owner_codes:
            entry: Optional[StateGioEntry] = self._find_unclaimed_entry_for_owner(owner_code)
            if entry is None:
                continue

            entry.claimed = True
            return self._apply_state_frbr(new_gio, entry.state_gio)

        return new_gio

    def _find_unclaimed_entry_for_owner(self, owner_code: str) -> Optional[StateGioEntry]:
        for entry in self._entries:
            if not entry.claimed and owner_code in entry.used_by:
                return entry
        return None

    def _apply_state_frbr(self, new_gio: PublicationGio, state_gio: models.Gio) -> PublicationGio:
        if self._gio_data_is_same(new_gio, state_gio):
            # Unchanged: reuse the state gio's FRBR as-is (same version).
            new_gio.new = False
            new_gio.geboorteregeling = state_gio.geboorteregeling
            new_gio.achtergrond_verwijzing = state_gio.achtergrond_verwijzing
            new_gio.achtergrond_actualiteit = state_gio.achtergrond_actualiteit

            new_gio.frbr = dso_models.GioFRBR.model_validate(state_gio.frbr.model_dump())
        else:
            # Changed: keep the same FRBR Work (the lineage) but a new expression.
            new_gio.new = True
            new_gio.geboorteregeling = state_gio.geboorteregeling
            new_gio.frbr.Work_Province_ID = state_gio.frbr.Work_Province_ID
            new_gio.frbr.Work_Date = state_gio.frbr.Work_Date
            new_gio.frbr.Work_Other = state_gio.frbr.Work_Other
            new_gio.frbr.Expression_Version = state_gio.frbr.Expression_Version + 1

        return new_gio

    def _gio_data_is_same(self, new_gio: PublicationGio, state_gio: models.Gio) -> bool:
        if state_gio.source_codes != new_gio.source_codes:
            return False

        state_hashes: Set[str] = {location.source_hash for location in state_gio.locaties}
        new_hashes: Set[str] = {location.source_hash for location in new_gio.locaties}

        return state_hashes == new_hashes

    def get_removed_state_gios(self) -> List[models.Gio]:
        # Unclaimed state gios are no longer used and must be withdrawn.
        return [entry.state_gio for entry in self._entries if not entry.claimed]


class PatchActMutation:
    def __init__(self, asset_provider: PublicationAssetProvider, active_act: models.ActiveAct):
        self._asset_provider: PublicationAssetProvider = asset_provider
        self._active_act: models.ActiveAct = active_act
        self._gio_pool: StateGioPool = StateGioPool(active_act)

    def patch(self, session: Session, data: ApiActInputData) -> ApiActInputData:
        data = self._patch_gios(data)
        data = self._patch_documents(data)
        data = self._patch_assets(session, data)
        data = self._patch_act_mutation(data)
        data = self._patch_ow_state(data)
        return data

    def _patch_gios(self, data: ApiActInputData) -> ApiActInputData:
        gios: Dict[str, PublicationGio] = data.Publication_Data.gios

        for gio_key, new_gio in gios.items():
            owner_codes: List[str] = self._owner_codes_for_gio(data, gio_key)
            gios[gio_key] = self._gio_pool.claim(new_gio, owner_codes)

        # After patching the GIOs, we need to restore the original basisgeo_ids on the locaties.
        #
        # During publication, new basisgeo_ids are generated for all gebieden (before they are
        # resolved into locaties). At the moment we patch the GIOs above, we cannot reliably
        # reuse the old basisgeo_ids because the number and ordering of locaties may differ
        # between the existing ("was") and new data.
        #
        # To handle this safely, we first collect all existing locaties into a lookup map
        # keyed by source_hash -> basisgeo_id. We then iterate over the new data and, where
        # a matching source_hash exists, overwrite the generated basisgeo_id with the
        # original one to preserve identity across versions.
        state_hash_map: Dict[str, str] = {}
        for state_gio in self._active_act.Gios.values():
            for state_location in state_gio.locaties:
                state_hash_map[state_location.source_hash] = state_location.basisgeo_id

        # Now reuse those basisgeo_ids where we can
        for gio_key, new_gio in gios.items():
            for loc_index, location in enumerate(new_gio.locaties):
                basisgeo_id: str = state_hash_map.get(location.source_hash, location.basisgeo_id)
                location.basisgeo_id = basisgeo_id
                new_gio.locaties[loc_index] = location
            gios[gio_key] = new_gio

        data.Publication_Data.gios = gios

        return data

    def _owner_codes_for_gio(self, data: ApiActInputData, gio_key: str) -> List[str]:
        # Owners are ordered by priority: gebiedengroepen first (sorted by
        # code), then gebiedsaanwijzingen (sorted by code). So when a new gio
        # is shared by owners that previously pointed to different state gios,
        # the gebiedengroep lineage wins deterministically.
        owner_codes: List[str] = []

        gebiedengroepen = data.Publication_Data.gebiedengroepen.values()
        for groep in sorted(gebiedengroepen, key=lambda g: g.code):
            if groep.gio_key == gio_key:
                owner_codes.append(groep.code)

        gebiedsaanwijzingen = data.Publication_Data.gebiedsaanwijzingen.values()
        for aanwijzing in sorted(gebiedsaanwijzingen, key=lambda a: a.code):
            if aanwijzing.gio_key == gio_key:
                owner_codes.append(aanwijzing.code)

        return owner_codes

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
            Removed_Gios=self._get_removed_gios(),
        )
        return data

    def _get_removed_gios(self) -> List[dict]:
        removed_gios: List[dict] = []

        for state_gio in self._gio_pool.get_removed_state_gios():
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
