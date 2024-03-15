from typing import List, Optional, Set

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
        work_date: str = f"{werkingsgebied['Created_Date'].year}"
        work_identifier = str(werkingsgebied["Object_ID"])
        work: str = f"/join/id/regdata/{act_frbr.Work_Province_ID}/{work_date}/{work_identifier}"

        date_version: str = werkingsgebied["Modified_Date"].strftime("%Y-%m-%d;%H%M")
        expression_version: str = f"{act_frbr.Expression_Language}@{date_version}"

        result = {
            "UUID": werkingsgebied["UUID"],
            "Object_ID": werkingsgebied["Object_ID"],
            "Code": werkingsgebied["Code"],
            "New": True,
            "Work": work,
            "Expression_Version": expression_version,
            "Title": area.Source_Title,
            "Symbol": area.Source_Symbol,
            "Achtergrond_Verwijzing": "TOP10NL",
            "Achtergrond_Actualiteit": str(werkingsgebied["Modified_Date"])[:10],
            "Onderverdelingen": [
                {
                    "UUID": werkingsgebied["UUID"],
                    "Title": area.Source_Title,
                    "Symbol": area.Source_Symbol,
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
