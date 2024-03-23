from datetime import datetime
from typing import List, Optional, Set

import dso.models as dso_models

from app.extensions.areas.db.tables import AreasTable
from app.extensions.areas.repository.area_repository import AreaRepository
from app.extensions.publications.models.api_input_data import ActFrbr


class PublicationWerkingsgebiedenProvider:
    def __init__(self, area_repository: AreaRepository):
        self._area_repository: AreaRepository = area_repository

    def get_werkingsgebieden(
        self,
        act_frbr: ActFrbr,
        all_objects: List[dict],
        used_obejcts: List[dict],
    ) -> List[dict]:
        werkingsgebieden_objects: List[dict] = [o for o in all_objects if o["Object_Type"] == "werkingsgebied"]
        werkingsgebied_codes: Set[str] = self._calculate_werkingsgebied_codes(used_obejcts)
        used_werkingsgebieden_objects: List[str] = [
            w for w in werkingsgebieden_objects if w["Code"] in werkingsgebied_codes
        ]

        werkingsgebieden: List[dict] = self._get_werkingsgebieden_with_areas(
            act_frbr,
            used_werkingsgebieden_objects,
        )
        return werkingsgebieden

    def _get_werkingsgebieden_with_areas(
        self,
        act_frbr: ActFrbr,
        werkingsgebieden_objects: List[dict],
    ) -> List[dict]:
        result: List[dict] = []

        for werkingsgebied in werkingsgebieden_objects:
            code = werkingsgebied["Code"]
            area_uuid = werkingsgebied["Area_UUID"]
            if area_uuid is None:
                raise RuntimeError(f"Missing area for werkingsgebied with code: {code}")

            area: Optional[AreasTable] = self._area_repository.get_with_gml(area_uuid)
            if area is None:
                raise RuntimeError(f"Area UUID does not exists for code: {code}")

            dso_werkingsgebied: dict = self._as_dso_werkingsgebied(act_frbr, werkingsgebied, area)
            result.append(dso_werkingsgebied)

        return result

    def _as_dso_werkingsgebied(
        self,
        act_frbr: ActFrbr,
        werkingsgebied: dict,
        area: AreasTable,
    ) -> dict:
        # We build it so that werkingsgebieden are consolidated per Act
        # Therefor their Work_Date is the acts Work_Date
        # And their identifier is made unique with acts data
        work_date: str = act_frbr.Work_Date
        work_identifier = f"{act_frbr.Act_ID}-{werkingsgebied['Object_ID']}"

        # Some of these expression values are set as if this is the first version
        # But should be overwritten by the state system if they are already published under this UUID
        frbr = dso_models.GioFRBR(
            Work_Province_ID=act_frbr.Work_Province_ID,
            Work_Date=work_date,
            Work_Other=work_identifier,
            Expression_Language=act_frbr.Expression_Language,
            Expression_Date=datetime.utcnow().strftime("%Y-%m-%d"),
            Expression_Version=1,
        )

        result = {
            "UUID": werkingsgebied["UUID"],
            "Object_ID": werkingsgebied["Object_ID"],
            "Code": werkingsgebied["Code"],
            "New": True,
            "Frbr": frbr,
            "Title": area.Source_Title,
            "Geboorteregeling": act_frbr.get_work(),
            "Achtergrond_Verwijzing": "TOP10NL",
            "Achtergrond_Actualiteit": str(werkingsgebied["Modified_Date"])[:10],
            "Onderverdelingen": [
                {
                    "UUID": werkingsgebied["UUID"],
                    "Title": area.Source_Title,
                    "Gml": area.Gml,
                }
            ],
        }
        return result

    def _calculate_werkingsgebied_codes(self, used_objects: List[dict]) -> Set[str]:
        werkingsgebied_codes: Set[str] = set(
            [o.get("Werkingsgebied_Code") for o in used_objects if o.get("Werkingsgebied_Code", None) is not None]
        )
        return werkingsgebied_codes
