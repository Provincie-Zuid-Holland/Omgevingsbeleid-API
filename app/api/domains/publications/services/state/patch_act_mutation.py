from typing import Dict, List, Optional, Set
from uuid import UUID

from sqlalchemy.orm import Session

from app.api.domains.publications.services.assets.publication_asset_provider import PublicationAssetProvider
from app.api.domains.publications.services.state.versions.v5 import models
from app.api.domains.publications.types.api_input_data import ActFrbr, ActMutation, ApiActInputData


class PatchActMutation:
    def __init__(self, asset_provider: PublicationAssetProvider, active_act: models.ActiveAct):
        self._asset_provider: PublicationAssetProvider = asset_provider
        self._active_act: models.ActiveAct = active_act

    def patch(self, session: Session, data: ApiActInputData) -> ApiActInputData:
        data = self._patch_werkingsgebieden(data)
        data = self._patch_documents(data)
        data = self._patch_assets(session, data)
        data = self._patch_act_mutation(data)
        data = self._patch_ow_state(data)
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
            if self._werkingsgebied_is_same(existing_werkingsgebied, werkingsgebied):
                werkingsgebieden[index]["New"] = False
                werkingsgebieden[index]["UUID"] = existing_werkingsgebied.UUID
                werkingsgebieden[index]["Identifier"] = existing_werkingsgebied.Identifier
                werkingsgebieden[index]["Geboorteregeling"] = existing_werkingsgebied.Owner_Act

                # Update the locations based on the state data
                existing_location_lookup = {loc.UUID: loc.model_dump() for loc in existing_werkingsgebied.Locations}
                werkingsgebieden[index]["Locaties"] = [
                    {**location, **existing_location_lookup.get(location["UUID"], {})}
                    for location in werkingsgebied["Locaties"]
                ]

                # Keep the same FRBR
                werkingsgebieden[index]["Frbr"].Work_Province_ID = existing_werkingsgebied.Frbr.Work_Province_ID
                werkingsgebieden[index]["Frbr"].Work_Date = existing_werkingsgebied.Frbr.Work_Date
                werkingsgebieden[index]["Frbr"].Work_Other = existing_werkingsgebied.Frbr.Work_Other
                werkingsgebieden[index]["Frbr"].Expression_Language = existing_werkingsgebied.Frbr.Expression_Language
                werkingsgebieden[index]["Frbr"].Expression_Date = existing_werkingsgebied.Frbr.Expression_Date
                werkingsgebieden[index]["Frbr"].Expression_Version = existing_werkingsgebied.Frbr.Expression_Version
            else:
                # If the hash are different that we will publish this as a new version
                werkingsgebieden[index]["New"] = True
                werkingsgebieden[index]["Geboorteregeling"] = existing_werkingsgebied.Owner_Act
                # Keep the same FRBR Work, but new expression
                werkingsgebieden[index]["Frbr"].Work_Province_ID = existing_werkingsgebied.Frbr.Work_Province_ID
                werkingsgebieden[index]["Frbr"].Work_Date = existing_werkingsgebied.Frbr.Work_Date
                werkingsgebieden[index]["Frbr"].Work_Other = existing_werkingsgebied.Frbr.Work_Other
                werkingsgebieden[index]["Frbr"].Expression_Version = existing_werkingsgebied.Frbr.Expression_Version + 1

        data.Publication_Data.werkingsgebieden = werkingsgebieden

        return data

    def _werkingsgebied_is_same(self, existing: models.Werkingsgebied, werkingsgebied: dict) -> bool:
        if not existing.is_still_valid():
            return False

        return str(werkingsgebied["Hash"]) == existing.Hash

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
                "Frbr": state_werkingsgebied.Frbr.model_dump(),
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

    def _patch_ow_state(self, data: ApiActInputData) -> ApiActInputData:
        data.Ow_State = self._active_act.Ow_State.model_dump_json()
        return data
