from typing import List, Set

from app.extensions.areas.repository.area_geometry_repository import AreaGeometryRepository


class PublicationWerkingsgebiedenProvider:
    def __init__(self, geometry_repository: AreaGeometryRepository):
        self._area_geometry_repository: AreaGeometryRepository = geometry_repository

    def get_werkingsgebieden(
        self,
        all_objects: List[dict],
        used_obejcts: List[dict],
    ) -> List[dict]:
        werkingsgebieden_objects: List[dict] = [o for o in all_objects if o["Object_Type"] == "werkingsgebied"]
        werkingsgebied_codes: Set[str] = self._calculate_werkingsgebied_codes(used_obejcts)
        used_werkingsgebieden_objects: List[str] = [
            w for w in werkingsgebieden_objects if w["Code"] in werkingsgebied_codes
        ]

        werkingsgebieden: List[dict] = self._get_werkingsgebieden_with_areas(used_werkingsgebieden_objects)
        return werkingsgebieden

    def _get_werkingsgebieden_with_areas(self, werkingsgebieden_objects: List[dict]) -> List[dict]:
        result: List[dict] = []

        for werkingsgebied in werkingsgebieden_objects:
            code = werkingsgebied["Code"]
            area_uuid = werkingsgebied["Area_UUID"]
            if area_uuid is None:
                raise RuntimeError(f"Missing area for werkingsgebied with code: {code}")
            area: dict = self._area_geometry_repository.get_area(area_uuid)

            dso_werkingsgebied: dict = self._as_dso_werkingsgebied(werkingsgebied, area)
            result.append(dso_werkingsgebied)

        return result

    def _as_dso_werkingsgebied(self, werkingsgebied: dict, area: dict) -> dict:
        result = {
            "UUID": werkingsgebied["UUID"],
            "Object_ID": werkingsgebied["Object_ID"],
            "Object_Type": werkingsgebied["Object_Type"],
            "Code": werkingsgebied["Code"],
            "Title": area["Source_Title"],
            "Symbol": area["Source_Symbol"],
            "Created_Date": str(werkingsgebied["Created_Date"]),
            "Modified_Date": str(werkingsgebied["Modified_Date"]),
            "Achtergrond_Verwijzing": "TOP10NL",
            "Achtergrond_Actualiteit": str(werkingsgebied["Modified_Date"])[:10],
            "Onderverdelingen": [
                {
                    "UUID": werkingsgebied["UUID"],
                    "Title": area["Source_Title"],
                    "Symbol": area["Source_Symbol"],
                    "Geometry": area["Shape"],
                    "Created_Date": str(werkingsgebied["Created_Date"]),
                    "Modified_Date": str(werkingsgebied["Modified_Date"]),
                }
            ],
        }
        return result

    def _calculate_werkingsgebied_codes(self, used_objects: List[dict]) -> Set[str]:
        werkingsgebied_codes: Set[str] = set(
            [o.get("Werkingsgebied_Code") for o in used_objects if o.get("Werkingsgebied_Code", None) is not None]
        )
        return werkingsgebied_codes
