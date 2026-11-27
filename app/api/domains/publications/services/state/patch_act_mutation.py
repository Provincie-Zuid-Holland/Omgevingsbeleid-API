from uuid import UUID

import dso.models as dso_models
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.publications.services.assets.publication_asset_provider import PublicationAssetProvider
from app.api.domains.publications.services.state.versions import active_models
from app.api.domains.publications.types.api_input_data import ActFrbr, ActMutation, ApiActInputData, PublicationGio


# used_by: owner codes (gebiedengroep / gebiedsaanwijzing) that referenced
# this state gio in the previous publication. A state gio is claimed at most
# once, by the first new gio that reuses its lineage.
class StateGioEntry(BaseModel):
    used_by: set[str]
    state_gio: active_models.Gio
    claimed: bool = False


class StateGioPool:
    """
    Tracks the gios of the previous publication so a new gio can reuse their
    FRBR lineage instead of building a brand new gio.

    The stable identity across publications is the owner code
    (gebiedengroep / gebiedsaanwijzing), not the gio key (which is rebuilt
    every publication and so changes every time). So we match by owner: a
    new gio inherits the state gio that one of its owners referenced last
    time.

    Each state gio can be claimed at most once: every owner code appears in
    the `used_by` of at most one state gio, and `claim` keeps the first
    priority owner whose state gio is still unclaimed.

    A state gio that nobody claims is no longer used and is withdrawn via
    `get_removed_state_gios`. This is the intended path for two cases:
    (1) the owner is gone from the new publication;
    (2) two owners that previously had different state gios are now merged into one new gio
    (their data is the same in this publication) — only the priority owner's
    lineage is claimed, and the other state gios those owners used end up
    withdrawn.
    """

    def __init__(self, active_act: active_models.ActiveAct):
        self._entries: list[StateGioEntry] = []
        for gio_key, state_gio in active_act.gios.items():
            used_by: set[str] = set()
            for groep in active_act.gebiedengroepen.values():
                if groep.gio_key == gio_key:
                    used_by.add(groep.code)
            for aanwijzing in active_act.gebiedsaanwijzingen.values():
                if aanwijzing.gio_key == gio_key:
                    used_by.add(aanwijzing.code)

            self._entries.append(
                StateGioEntry(
                    used_by=used_by,
                    state_gio=state_gio,
                )
            )

    def claim(self, new_gio: PublicationGio, owner_codes: list[str]) -> PublicationGio:
        """
        `owner_codes` must be ordered by priority: the first owner whose
        state gio is still unclaimed wins. Without a usable state gio
        `new_gio` is returned unchanged, keeping its own new FRBR.
        """
        for owner_code in owner_codes:
            entry: StateGioEntry | None = self._find_unclaimed_entry_for_owner(owner_code)
            if entry is None:
                continue

            entry.claimed = True
            return self._apply_state_frbr(new_gio, entry.state_gio)

        return new_gio

    def _find_unclaimed_entry_for_owner(self, owner_code: str) -> StateGioEntry | None:
        for entry in self._entries:
            if not entry.claimed and owner_code in entry.used_by:
                return entry
        return None

    def _apply_state_frbr(self, new_gio: PublicationGio, state_gio: active_models.Gio) -> PublicationGio:
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
            new_gio.frbr.work_province_id = state_gio.frbr.work_province_id
            new_gio.frbr.work_date = state_gio.frbr.work_date
            new_gio.frbr.work_other = state_gio.frbr.work_other
            new_gio.frbr.expression_version = state_gio.frbr.expression_version + 1

        return new_gio

    def _gio_data_is_same(self, new_gio: PublicationGio, state_gio: active_models.Gio) -> bool:
        if state_gio.title != new_gio.title:
            return False

        state_locs = {(location.title, location.source_hash) for location in state_gio.locaties}
        new_locs = {(location.title, location.source_hash) for location in new_gio.locaties}

        return state_locs == new_locs

    def get_removed_state_gios(self) -> list[active_models.Gio]:
        # Unclaimed state gios are no longer used and must be withdrawn.
        return [entry.state_gio for entry in self._entries if not entry.claimed]


class PatchActMutation:
    def __init__(self, asset_provider: PublicationAssetProvider, active_act: active_models.ActiveAct):
        self._asset_provider: PublicationAssetProvider = asset_provider
        self._active_act: active_models.ActiveAct = active_act
        self._gio_pool: StateGioPool = StateGioPool(active_act)

    async def patch(self, session: AsyncSession, data: ApiActInputData) -> ApiActInputData:
        data = self._patch_gios(data)
        data = self._patch_documents(data)
        data = await self._patch_assets(session, data)
        data = self._patch_act_mutation(data)
        data = self._patch_ow_state(data)
        return data

    def _patch_gios(self, data: ApiActInputData) -> ApiActInputData:
        gios: dict[str, PublicationGio] = data.publication_data.gios

        for gio_key, new_gio in gios.items():
            owner_codes: list[str] = self._owner_codes_for_gio(data, gio_key)
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
        state_hash_map: dict[str, str] = {}
        for state_gio in self._active_act.gios.values():
            for state_location in state_gio.locaties:
                state_hash_map[state_location.source_hash] = state_location.basisgeo_id

        # Now reuse those basisgeo_ids where we can
        for gio_key, new_gio in gios.items():
            for loc_index, location in enumerate(new_gio.locaties):
                basisgeo_id: str = state_hash_map.get(location.source_hash, location.basisgeo_id)
                location.basisgeo_id = basisgeo_id
                new_gio.locaties[loc_index] = location
            gios[gio_key] = new_gio

        data.publication_data.gios = gios

        return data

    def _owner_codes_for_gio(self, data: ApiActInputData, gio_key: str) -> list[str]:
        # Owners are ordered by priority: gebiedengroepen first (sorted by
        # code), then gebiedsaanwijzingen (sorted by code). So when a new gio
        # is shared by owners that previously pointed to different state gios,
        # the gebiedengroep lineage wins deterministically.
        owner_codes: list[str] = []

        gebiedengroepen = data.publication_data.gebiedengroepen.values()
        for groep in sorted(gebiedengroepen, key=lambda g: g.code):
            if groep.gio_key == gio_key:
                owner_codes.append(groep.code)

        gebiedsaanwijzingen = data.publication_data.gebiedsaanwijzingen.values()
        for aanwijzing in sorted(gebiedsaanwijzingen, key=lambda a: a.code):
            if aanwijzing.gio_key == gio_key:
                owner_codes.append(aanwijzing.code)

        return owner_codes

    def _patch_documents(self, data: ApiActInputData) -> ApiActInputData:
        state_documents: dict[int, active_models.Document] = self._active_act.documents

        documents: list[dict] = data.publication_data.documents
        for index, document in enumerate(documents):
            object_id: int = document["object_id"]
            existing_document: active_models.Document | None = state_documents.get(object_id)
            if existing_document is None:
                continue

            # If the hashes are the same, then we use the state data
            # and define the document as not new
            if str(document["hash"]) == existing_document.hash:
                documents[index]["new"] = False
                documents[index]["id"] = existing_document.id
                documents[index]["geboorteregeling"] = existing_document.owner_act
                # Keep the same FRBR
                documents[index]["frbr"].work_province_id = existing_document.frbr.work_province_id
                documents[index]["frbr"].work_date = existing_document.frbr.work_date
                documents[index]["frbr"].work_other = existing_document.frbr.work_other
                documents[index]["frbr"].expression_language = existing_document.frbr.expression_language
                documents[index]["frbr"].expression_date = existing_document.frbr.expression_date
                documents[index]["frbr"].expression_version = existing_document.frbr.expression_version
            else:
                # If the hash are different that we will publish this as a new version
                documents[index]["new"] = True
                documents[index]["geboorteregeling"] = existing_document.owner_act
                # Keep the same FRBR Work, but new expression
                documents[index]["frbr"].work_province_id = existing_document.frbr.work_province_id
                documents[index]["frbr"].work_date = existing_document.frbr.work_date
                documents[index]["frbr"].work_other = existing_document.frbr.work_other
                documents[index]["frbr"].expression_version = existing_document.frbr.expression_version + 1

        data.publication_data.documents = documents

        return data

    def _gebiedengroep_is_same(self, existing: active_models.Gebiedengroep, gebiedengroep: dict) -> bool:
        return gebiedengroep["code"] == existing.code

    async def _patch_assets(self, session: AsyncSession, data: ApiActInputData) -> ApiActInputData:
        state_assets: dict[str, active_models.Asset] = self._active_act.assets

        fetched_assets_ids: set[str] = {a["id"] for a in data.publication_data.assets}
        additional_asset_ids_str: set[str] = {
            sa.id for _, sa in state_assets.items() if sa.id not in fetched_assets_ids
        }
        additional_asset_ids: list[UUID] = [UUID(uuid_str) for uuid_str in additional_asset_ids_str]
        additional_assets: list[dict] = await self._asset_provider.get_assets_by_ids(session, additional_asset_ids)

        data.publication_data.assets = data.publication_data.assets + additional_assets

        return data

    def _patch_act_mutation(self, data: ApiActInputData) -> ApiActInputData:
        consolidated_frbr: ActFrbr = ActFrbr(
            act_id=0,
            work_province_id=self._active_act.act_frbr.work_province_id,
            work_country=self._active_act.act_frbr.work_country,
            work_date=self._active_act.act_frbr.work_date,
            work_other=self._active_act.act_frbr.work_other,
            expression_language=self._active_act.act_frbr.expression_language,
            expression_date=self._active_act.act_frbr.expression_date,
            expression_version=self._active_act.act_frbr.expression_version,
        )
        data.act_mutation = ActMutation(
            consolidated_act_frbr=consolidated_frbr,
            consolidated_act_text=self._active_act.act_text,
            known_wid_map=self._active_act.wid_data.known_wid_map,
            known_wids=self._active_act.wid_data.known_wids,
            removed_gios=self._get_removed_gios(),
        )
        return data

    def _get_removed_gios(self) -> list[dict]:
        removed_gios: list[dict] = []

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
        data.ow_state = self._active_act.ow_state.model_dump_json()
        return data
