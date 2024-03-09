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

        # @todo: remove
        # area["Shape"] = "POLYGON ((74567.347600001842 443493.91890000325, 74608.622699998392 443619.86080000486, 74661.431899998352 443796.90439999942, 74657.325500000254 443794.78040000005, 74664.067999999956 443810.51300000178, 74729.171500001146 444013.33940000291, 74754.307000000073 444217.06900000118, 74766.111800000086 444287.24220000062, 74700.32570000003 444274.74290000094, 74617.775499999538 444246.9616000005, 74514.7938000001 444196.70150000026, 74448.482099998742 444165.69250000105, 74333.605200000064 444112.87550000072, 74204.86380000037 444067.32080000057, 74148.195700000957 444071.55770000169, 74232.0122999996 443919.14220000163, 74294.7186000012 443819.92320000188, 74402.363600000725 443672.54520000424, 74411.650600001187 443659.83020000259, 74518.027399998187 443515.38720000343, 74567.347600001842 443493.91890000325))"

        result = {
            "UUID": werkingsgebied["UUID"],
            "Object_ID": werkingsgebied["Object_ID"],
            "Object_Type": werkingsgebied["Object_Type"],
            "Code": werkingsgebied["Code"],
            "New": True,
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
