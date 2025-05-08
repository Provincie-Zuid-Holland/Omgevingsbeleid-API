import uuid
from typing import Any, Dict, Optional, Tuple

import app.api.domains.publications.services.state.versions.v2.models as models_v2
from app.api.domains.publications.repository.publication_act_package_repository import PublicationActPackageRepository
from app.api.domains.publications.repository.publication_act_version_repository import PublicationActVersionRepository
from app.api.domains.publications.services.act_package.act_publication_data_provider import ActPublicationDataProvider
from app.api.domains.publications.services.state import State
from app.api.domains.publications.services.state.state_upgrader import StateUpgrader
from app.api.domains.publications.types.api_input_data import ActFrbr, BillFrbr, PublicationData
from app.core.tables.publications import PublicationActPackageTable, PublicationActVersionTable

from ..v1 import state_v1
from ..v2 import state_v2


class StateV2Upgrader(StateUpgrader):
    def __init__(
        self,
        act_version_repository: PublicationActVersionRepository,
        act_package_repository: PublicationActPackageRepository,
        act_data_provider: ActPublicationDataProvider,
    ):
        self._act_version_repository: PublicationActVersionRepository = act_version_repository
        self._act_package_repository: PublicationActPackageRepository = act_package_repository
        self._act_data_provider: ActPublicationDataProvider = act_data_provider

    @staticmethod
    def get_input_schema_version() -> int:
        return state_v1.StateV1.get_schema_version()

    def upgrade(self, environment_uuid: uuid.UUID, old_state: State) -> State:
        if old_state.get_schema_version() != state_v1.StateV1.get_schema_version():
            raise RuntimeError("Unexpected state provided")

        if not isinstance(old_state, state_v1.StateV1):
            raise RuntimeError("Unexpected state provided")

        purposes = self._mutate_purposes(old_state)
        acts = self._mutate_acts(environment_uuid, old_state)
        announcements = self._mutate_announcements(old_state)

        new_state = state_v2.StateV2(
            Purposes=purposes,
            Acts=acts,
            Announcements=announcements,
        )

        return new_state

    def _mutate_purposes(self, old_state: state_v1.StateV1) -> Dict[str, models_v2.Purpose]:
        purposes: Dict[str, models_v2.Purpose] = {}

        for key, old_purpose in old_state.Purposes.items():
            new_purpose: models_v2.Purpose = models_v2.Purpose.model_validate(old_purpose.model_dump())
            purposes[key] = new_purpose

        return purposes

    def _mutate_acts(self, environment_uuid: uuid.UUID, old_state: state_v1.StateV1) -> Dict[str, models_v2.ActiveAct]:
        acts: Dict[str, models_v2.ActiveAct] = {}

        for key, old_act in old_state.Acts.items():
            new_act: models_v2.ActiveAct = self._mutate_act(environment_uuid, old_act)
            acts[key] = new_act

        return acts

    def _mutate_act(self, environment_uuid: uuid.UUID, old_act: state_v1.ActiveAct) -> models_v2.ActiveAct:
        original_data, publication_version_uuid = self._get_original_input_data(environment_uuid, old_act)

        werkingsgebieden: Dict[int, models_v2.Werkingsgebied] = self._get_act_werkingsgebieden(
            original_data,
            old_act,
        )

        ow_data: models_v2.OwData = self._get_act_ow_data(original_data, old_act)

        act = models_v2.ActiveAct(
            Act_Frbr=models_v2.Frbr.model_validate(old_act.Act_Frbr.model_dump()),
            Bill_Frbr=models_v2.Frbr.model_validate(old_act.Bill_Frbr.model_dump()),
            Consolidation_Purpose=models_v2.Purpose.model_validate(old_act.Consolidation_Purpose.model_dump()),
            Document_Type=old_act.Document_Type,
            Procedure_Type=old_act.Procedure_Type,
            Werkingsgebieden=werkingsgebieden,
            Wid_Data=models_v2.WidData.model_validate(old_act.Wid_Data.model_dump()),
            Ow_Data=ow_data,
            Act_Text=old_act.Act_Text,
            Publication_Version_UUID=str(publication_version_uuid),
        )
        return act

    def _get_act_werkingsgebieden(
        self, original_data: PublicationData, old_act: state_v1.ActiveAct
    ) -> Dict[int, models_v2.Werkingsgebied]:
        new_werkingsgebieden: Dict[int, models_v2.Werkingsgebied] = {}

        for key, old_werkingsgebied in old_act.Werkingsgebieden.items():
            original_werkingsgebied: Optional[dict] = next(
                (w for w in original_data.werkingsgebieden if w["Object_ID"] == old_werkingsgebied.Object_ID),
                {
                    "Title": "",
                    "Hash": "",
                },
            )

            data_dict = old_werkingsgebied.model_dump()
            data_dict["Title"] = original_werkingsgebied["Title"]
            data_dict["Hash"] = original_werkingsgebied["Hash"]

            new_werkingsgebied = models_v2.Werkingsgebied.model_validate(data_dict)
            new_werkingsgebieden[key] = new_werkingsgebied

        return new_werkingsgebieden

    def _get_original_input_data(
        self, environment_uuid: uuid.UUID, old_act: state_v1.ActiveAct
    ) -> Tuple[PublicationData, uuid.UUID]:
        act_version: Optional[PublicationActVersionTable] = self._act_version_repository.get_by_work_expression(
            environment_uuid,
            old_act.Document_Type,
            old_act.Procedure_Type,
            old_act.Act_Frbr.Work_Province_ID,
            old_act.Act_Frbr.Work_Country,
            old_act.Act_Frbr.Work_Date,
            old_act.Act_Frbr.Work_Other,
            old_act.Act_Frbr.Expression_Language,
            old_act.Act_Frbr.Expression_Date,
            old_act.Act_Frbr.Expression_Version,
        )
        if act_version is None:
            raise RuntimeError("PublicationActVersionTable not found while upgrading state1 to state2")

        act_package: Optional[PublicationActPackageTable] = self._act_package_repository.get_by_act_version(
            act_version.UUID,
        )
        if act_package is None:
            raise RuntimeError("PublicationActPackageTable not found while upgrading state1 to state2")

        fake_bill = BillFrbr(
            Work_Province_ID=old_act.Bill_Frbr.Work_Province_ID,
            Work_Country=old_act.Bill_Frbr.Work_Country,
            Work_Date=old_act.Bill_Frbr.Work_Date,
            Work_Other=old_act.Bill_Frbr.Work_Other,
            Expression_Language=old_act.Bill_Frbr.Expression_Language,
            Expression_Date=old_act.Bill_Frbr.Expression_Date,
            Expression_Version=old_act.Bill_Frbr.Expression_Version,
        )
        fake_act = ActFrbr(
            Act_ID=0,
            Work_Province_ID=old_act.Act_Frbr.Work_Province_ID,
            Work_Country=old_act.Act_Frbr.Work_Country,
            Work_Date=old_act.Act_Frbr.Work_Date,
            Work_Other=old_act.Act_Frbr.Work_Other,
            Expression_Language=old_act.Act_Frbr.Expression_Language,
            Expression_Date=old_act.Act_Frbr.Expression_Date,
            Expression_Version=old_act.Act_Frbr.Expression_Version,
        )

        publication_data: PublicationData = self._act_data_provider.fetch_data(
            act_package.Publication_Version,
            fake_bill,
            fake_act,
            all_data=True,
        )
        return publication_data, act_package.Publication_Version.UUID

    def _mutate_announcements(self, old_state: state_v1.StateV1) -> Dict[str, models_v2.ActiveAnnouncement]:
        announcements: Dict[str, models_v2.ActiveAnnouncement] = {}

        for key, old_announcement in old_state.Announcements.items():
            new_announcement: models_v2.ActiveAnnouncement = models_v2.ActiveAnnouncement.model_validate(
                old_announcement.model_dump()
            )
            announcements[key] = new_announcement

        return announcements

    def _get_act_ow_data(self, original_data: PublicationData, old_act: state_v1.ActiveAct) -> models_v2.OwData:
        old_id_mapping: Dict[str, Dict[str, str]] = old_act.Ow_Data.Object_Map.id_mapping
        old_tekstdeel_mapping: Dict[str, Dict[str, str]] = old_act.Ow_Data.Object_Map.tekstdeel_mapping

        unknown_werkingsgebied = {
            "UUID": None,
            "Title": "",
            "Hash": None,
        }

        new_ow_objects: Dict[str, Any] = {}

        # Ambtsgebied / Area of Jurisdiction
        for uuidx_str, ow_id in old_id_mapping.get("ambtsgebied", {}).items():
            if uuid.UUID(uuidx_str) != original_data.area_of_jurisdiction["UUID"]:
                raise RuntimeError("AOJ.UUID does not match with original data")
            ow = {
                "OW_ID": ow_id,
                "status": None,
                "procedure_status": None,
                "mapped_uuid": str(original_data.area_of_jurisdiction["UUID"]),
                "noemer": original_data.area_of_jurisdiction["Title"],
                "bestuurlijke_grenzen_verwijzing": {
                    "bestuurlijke_grenzen_id": original_data.area_of_jurisdiction["Administrative_Borders_ID"],
                    "domein": original_data.area_of_jurisdiction["Administrative_Borders_Domain"],
                    "geldig_op": original_data.area_of_jurisdiction["Administrative_Borders_Date"].strftime("%Y-%m-%d"),
                },
                "ow_type": "OWAmbtsgebied",
            }
            new_ow_objects[ow_id] = ow

        # Regelinggebied
        for aoj_ow_id, ow_id in old_id_mapping.get("regelingsgebied", {}).items():
            ow = {
                "OW_ID": ow_id,
                "status": None,
                "procedure_status": None,
                "ambtsgebied": aoj_ow_id,
                "ow_type": "OWRegelingsgebied",
            }
            new_ow_objects[ow_id] = ow

        # Gebieden
        for werkingsgebied_code, ow_id in old_id_mapping.get("gebieden", {}).items():
            original_werkingsgebied: Optional[dict] = next(
                (w for w in original_data.werkingsgebieden if w["Code"] == werkingsgebied_code), unknown_werkingsgebied
            )

            ow = {
                "OW_ID": ow_id,
                "status": None,
                "procedure_status": None,
                "mapped_uuid": str(original_werkingsgebied["UUID"]),
                "noemer": original_werkingsgebied["Title"],
                "mapped_geo_code": werkingsgebied_code,
                "ow_type": "OWGebied",
            }
            new_ow_objects[ow_id] = ow

        # Gebiedengroep
        for werkingsgebied_code, ow_id in old_id_mapping.get("gebiedengroep", {}).items():
            original_werkingsgebied: Optional[dict] = next(
                (w for w in original_data.werkingsgebieden if w["Code"] == werkingsgebied_code), unknown_werkingsgebied
            )
            gebied_ow_id: Optional[str] = old_id_mapping.get("gebieden", {}).get(werkingsgebied_code)
            gebieden_ow_ids = [gebied_ow_id] if gebied_ow_id else []
            ow = {
                "OW_ID": ow_id,
                "status": None,
                "procedure_status": None,
                "mapped_uuid": str(original_werkingsgebied["UUID"]),
                "noemer": original_werkingsgebied["Title"],
                "mapped_geo_code": werkingsgebied_code,
                "gebieden": gebieden_ow_ids,
                "ow_type": "OWGebiedenGroep",
            }
            new_ow_objects[ow_id] = ow

        # Divisietekst
        for wid, ow_id in old_id_mapping.get("wid", {}).items():
            ow = {"OW_ID": ow_id, "status": None, "procedure_status": None, "wid": wid, "ow_type": "OWDivisieTekst"}
            # get key from old act Wid_Data.Known_Wid_map dict if wid matching this dicts value
            ow["mapped_policy_object_code"] = next(
                (k for k, v in old_act.Wid_Data.Known_Wid_Map.items() if v == wid), None
            )
            new_ow_objects[ow_id] = ow

        # Tekstdeel
        for ow_id, data in old_tekstdeel_mapping.items():
            ow = {
                "OW_ID": ow_id,
                "status": None,
                "procedure_status": None,
                "divisie": data["divisie"],
                "locaties": [
                    data["location"],
                ],
                "ow_type": "OWTekstdeel",
                "divisie_type": "divisietekst",
            }
            new_ow_objects[ow_id] = ow

        new_ow_data = models_v2.OwData(
            Ow_Objects=new_ow_objects,  # type: ignore
            Terminated_Ow_Ids=[],  # type: ignore
        )
        return new_ow_data
