from copy import deepcopy

import dso.models as dso_models
from dso.act_builder.builder import Builder
from dso.act_builder.services.ow.state.ow_state import OwState as DsoOwState

from app.api.domains.publications.services.state.versions import ActiveState, active_actions, active_models
from app.api.domains.publications.types.api_input_data import ApiActInputData, Purpose
from app.core.tables.publications import PublicationTable, PublicationVersionTable


class ActStatePatcher:
    def __init__(self, api_input_data: ApiActInputData, dso_builder: Builder):
        self._api_input_data: ApiActInputData = api_input_data
        self._dso_builder: Builder = dso_builder
        self._publication_version: PublicationVersionTable = api_input_data.publication_version
        self._publication: PublicationTable = api_input_data.publication_version.publication

    def apply(self, source_state: ActiveState) -> ActiveState:
        state: ActiveState = deepcopy(source_state)
        state = self._patch_publication(state)
        state = self._patch_consolidation_purpose(state)
        return state

    def _patch_publication(self, state: ActiveState) -> ActiveState:
        gios: dict[str, active_models.Gio] = self._resolve_gios(state)
        gebiedengroepen: dict[str, active_models.Gebiedengroep] = self._resolve_gebiedengroepen(state)
        gebiedsaanwijzingen: dict[str, active_models.Gebiedsaanwijzing] = self._resolve_gebiedsaanwijzingen(state)
        documents: dict[int, active_models.Document] = self._resolve_documents(state)
        wid_data = active_models.WidData(
            known_wid_map=self._dso_builder.get_used_wid_map(),
            known_wids=self._dso_builder.get_used_wids(),
        )

        # Serialize dso_ow_state to a simple dict for result model
        dso_ow_state: DsoOwState = self._dso_builder.get_ow_state()
        dso_ow_state_json: str = dso_ow_state.model_dump_json()
        ow_state = active_models.OwState.model_validate_json(dso_ow_state_json)

        input_purpose = self._api_input_data.consolidation_purpose
        effective_date: str | None = None
        if input_purpose.effective_date is not None:
            effective_date = input_purpose.effective_date.strftime("%Y-%m-%d")
        purpose = active_models.Purpose(
            purpose_type=input_purpose.purpose_type.value,
            effective_date=effective_date,
            work_province_id=input_purpose.work_province_id,
            work_date=input_purpose.work_date,
            work_other=input_purpose.work_other,
        )

        act_frbr = active_models.Frbr(
            work_province_id=self._api_input_data.act_frbr.work_province_id,
            work_country=self._api_input_data.act_frbr.work_country,
            work_date=self._api_input_data.act_frbr.work_date,
            work_other=self._api_input_data.act_frbr.work_other,
            expression_language=self._api_input_data.act_frbr.expression_language,
            expression_date=self._api_input_data.act_frbr.expression_date,
            expression_version=self._api_input_data.act_frbr.expression_version,
        )
        bill_frbr = active_models.Frbr(
            work_province_id=self._api_input_data.bill_frbr.work_province_id,
            work_country=self._api_input_data.bill_frbr.work_country,
            work_date=self._api_input_data.bill_frbr.work_date,
            work_other=self._api_input_data.bill_frbr.work_other,
            expression_language=self._api_input_data.bill_frbr.expression_language,
            expression_date=self._api_input_data.bill_frbr.expression_date,
            expression_version=self._api_input_data.bill_frbr.expression_version,
        )

        act_text: str | None = self._dso_builder.get_regeling_vrijetekst()
        if act_text is None:
            raise RuntimeError("Regeling vrijetekst bestaat niet")

        used_asset_ids: set[str] = self._dso_builder.get_asset_uuids_wordt()
        assets: dict[str, active_models.Asset] = {idx: active_models.Asset(id=idx) for idx in used_asset_ids}

        action = active_actions.AddPublicationAction(
            act_frbr=act_frbr,
            bill_frbr=bill_frbr,
            consolidation_purpose=purpose,
            document_type=self._api_input_data.publication_version.publication.document_type,
            procedure_type=self._api_input_data.publication_version.publication.procedure_type,
            gios=gios,
            gebiedengroepen=gebiedengroepen,
            gebiedsaanwijzingen=gebiedsaanwijzingen,
            documents=documents,
            assets=assets,
            wid_data=wid_data,
            ow_state=ow_state,
            act_text=act_text,
            publication_version_id=str(self._publication_version.id),
        )
        state.handle_action(action)
        return state

    def _resolve_gios(self, state: ActiveState) -> dict[str, active_models.Gio]:
        gios: dict[str, active_models.Gio] = {}

        # We only keep the send gios, as all other should have been withdrawn
        for dso_gio in self._api_input_data.publication_data.gios.values():
            dso_frbr: dso_models.FRBR = dso_gio.frbr
            frbr = active_models.Frbr(
                work_province_id=dso_frbr.work_province_id,
                work_country="",
                work_date=dso_frbr.work_date,
                work_other=dso_frbr.work_other,
                expression_language=dso_frbr.expression_language,
                expression_date=dso_frbr.expression_date,
                expression_version=dso_frbr.expression_version or 0,
            )

            locaties: list[active_models.GioLocatie] = [
                active_models.GioLocatie(
                    title=dso_locatie.title,
                    basisgeo_id=dso_locatie.basisgeo_id,
                    source_hash=dso_locatie.source_hash,
                    source_code=dso_locatie.code,
                )
                for dso_locatie in dso_gio.locaties
            ]

            gio = active_models.Gio(
                key=dso_gio.key,
                source_codes=dso_gio.source_codes,
                title=dso_gio.title,
                frbr=frbr,
                geboorteregeling=dso_gio.geboorteregeling,
                achtergrond_verwijzing=dso_gio.achtergrond_verwijzing,
                achtergrond_actualiteit=dso_gio.achtergrond_actualiteit,
                locaties=locaties,
            )
            gios[gio.key] = gio

        return gios

    def _resolve_gebiedengroepen(self, state: ActiveState) -> dict[str, active_models.Gebiedengroep]:
        gebiedengroepen: dict[str, active_models.Gebiedengroep] = {}

        # We only keep the send gebiedengroepen, as all other should have been withdrawn from the ow state
        for dso_gebiedengroep in self._api_input_data.publication_data.gebiedengroepen.values():
            gebiedengroep = active_models.Gebiedengroep(
                id=dso_gebiedengroep.id,
                code=dso_gebiedengroep.code,
                title=dso_gebiedengroep.title,
                source_gebieden_codes=dso_gebiedengroep.source_gebieden_codes,
                gio_key=dso_gebiedengroep.gio_key,
            )
            gebiedengroepen[gebiedengroep.code] = gebiedengroep

        return gebiedengroepen

    def _resolve_gebiedsaanwijzingen(self, state: ActiveState) -> dict[str, active_models.Gebiedsaanwijzing]:
        aanwijzingen: dict[str, active_models.Gebiedsaanwijzing] = {}

        # We only keep the send gebiedsaanwijzingen, as all other should have been withdrawn from the ow state
        for dso_aanwijzing in self._api_input_data.publication_data.gebiedsaanwijzingen.values():
            aanwijzing = active_models.Gebiedsaanwijzing(
                code=dso_aanwijzing.code,
                aanwijzing_type=dso_aanwijzing.aanwijzing_type,
                aanwijzing_group=dso_aanwijzing.aanwijzing_group,
                title=dso_aanwijzing.title,
                source_target_codes=dso_aanwijzing.source_target_codes,
                resolved_gebied_codes=dso_aanwijzing.resolved_gebied_codes,
                gio_key=dso_aanwijzing.gio_key,
            )
            aanwijzingen[aanwijzing.code] = aanwijzing

        return aanwijzingen

    def _resolve_documents(self, state: ActiveState) -> dict[int, active_models.Document]:
        documents: dict[int, active_models.Document] = {}

        # We only keep the send documents, as all other should have been withdrawn
        for dso_document in self._api_input_data.publication_data.documents:
            dso_frbr: dso_models.GioFRBR = dso_document["frbr"]
            frbr = active_models.Frbr(
                work_province_id=dso_frbr.work_province_id,
                work_country="",
                work_date=dso_frbr.work_date,
                work_other=dso_frbr.work_other,
                expression_language=dso_frbr.expression_language,
                expression_date=dso_frbr.expression_date,
                expression_version=dso_frbr.expression_version or 0,
            )
            document = active_models.Document(
                id=str(dso_document["id"]),
                code=str(dso_document["code"]),
                frbr=frbr,
                filename=dso_document["filename"],
                title=dso_document["title"],
                owner_act=dso_document["geboorteregeling"],
                content_type=dso_document["content_type"],
                object_id=dso_document["object_id"],
                hash=dso_document["hash"],
            )
            documents[document.object_id] = document

        return documents

    def _patch_consolidation_purpose(self, state: ActiveState) -> ActiveState:
        purpose: Purpose = self._api_input_data.consolidation_purpose
        action = active_actions.AddPurposeAction(
            purpose_type=purpose.purpose_type,
            effective_date=purpose.effective_date,
            work_province_id=purpose.work_province_id,
            work_date=purpose.work_date,
            work_other=purpose.work_other,
        )
        state.handle_action(action)
        return state
