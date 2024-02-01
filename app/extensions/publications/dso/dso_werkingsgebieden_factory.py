from typing import List, Set

from dso.builder.state_manager.input_data.resource.werkingsgebied.werkingsgebied_repository import (
    WerkingsgebiedRepository,
)

from app.extensions.areas.repository.area_geometry_repository import AreaGeometryRepository


class DsoWerkingsgebiedenFactory:
    def __init__(self, geometry_repository: AreaGeometryRepository):
        self._area_geometry_repository: AreaGeometryRepository = geometry_repository

    def get_repository_for_objects(
        self, werkingsgebieden_objects: List[dict], objects: List[dict]
    ) -> WerkingsgebiedRepository:
        werkingsgebied_codes: List[str] = self._calculate_werkingsgebied_codes(objects)
        used_werkingsgebieden_objects: List[str] = [
            w for w in werkingsgebieden_objects if w["Code"] in werkingsgebied_codes
        ]

        werkingsgebieden: List[dict] = self._get_werkingsgebieden_with_areas(used_werkingsgebieden_objects)
        repository: WerkingsgebiedRepository = self._create_repository(werkingsgebieden)
        return repository

    def _get_werkingsgebieden_with_areas(self, werkingsgebieden_objects: List[dict]) -> List[dict]:
        result: List[dict] = []
        for werkingsgebied in werkingsgebieden_objects:
            code = werkingsgebied["Code"]
            area_uuid = werkingsgebied["Area_UUID"]
            if area_uuid is None:
                print(f"\nMissing area for werkingsgebied {code}\n")
                continue
            area: dict = self._area_geometry_repository.get_area(area_uuid)

            dso_werkingsgebied: dict = self._as_werkingsgebied(werkingsgebied, area)
            result.append(dso_werkingsgebied)

        return result

    def _create_repository(self, werkingsgebieden: List[dict]) -> WerkingsgebiedRepository:
        repository = WerkingsgebiedRepository("pv28", "nld")
        for werkingsgebied in werkingsgebieden:
            repository.add(werkingsgebied)
        return repository

    def _as_werkingsgebied(self, werkingsgebied: dict, area: dict) -> dict:
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

    def _calculate_werkingsgebied_codes(self, objects: List[dict]) -> List[str]:
        werkingsgebied_codes: Set[str] = set(
            [o.get("Werkingsgebied_Code") for o in objects if o.get("Werkingsgebied_Code", None) is not None]
        )
        return list(werkingsgebied_codes)
