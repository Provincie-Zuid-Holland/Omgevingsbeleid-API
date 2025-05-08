import hashlib
import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Set

import dso.models as dso_models

from app.api.domains.publications.types.api_input_data import ActFrbr
from app.api.domains.werkingsgebieden.repositories.area_repository import AreaRepository
from app.core.tables.others import AreasTable


class PublicationWerkingsgebiedenProvider:
    def __init__(self, area_repository: AreaRepository):
        self._area_repository: AreaRepository = area_repository

    def get_werkingsgebieden(
        self,
        act_frbr: ActFrbr,
        all_objects: List[dict],
        used_objects: List[dict],
        all_data: bool = False,
    ) -> List[dict]:
        werkingsgebieden_objects: List[dict] = [o for o in all_objects if o["Object_Type"] == "werkingsgebied"]
        werkingsgebied_codes: Set[str] = self._calculate_werkingsgebied_codes(used_objects)
        used_werkingsgebieden_objects: List[dict] = [
            w for w in werkingsgebieden_objects if w["Code"] in werkingsgebied_codes or all_data
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
        work_identifier = f"{act_frbr.Act_ID}-{act_frbr.Expression_Version}-{werkingsgebied['Object_ID']}"

        # Some of these expression values are set as if this is the first version
        # But should be overwritten by the state system if they are already published under this UUID/Hash
        frbr = dso_models.GioFRBR(
            Work_Province_ID=act_frbr.Work_Province_ID,
            Work_Date=work_date,
            Work_Other=work_identifier,
            Expression_Language=act_frbr.Expression_Language,
            Expression_Date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            Expression_Version=1,
        )

        gml_hash = hashlib.sha512()
        gml_hash.update(area.Gml.encode())

        result = {
            "UUID": werkingsgebied["UUID"],
            "Identifier": str(uuid.uuid4()),
            "Hash": gml_hash.hexdigest(),
            "Object_ID": werkingsgebied["Object_ID"],
            "Code": werkingsgebied["Code"],
            "New": True,
            "Frbr": frbr,
            "Title": area.Source_Title,
            "Geboorteregeling": act_frbr.get_work(),
            "Achtergrond_Verwijzing": "TOP10NL",
            "Achtergrond_Actualiteit": str(werkingsgebied["Modified_Date"])[:10],
            "Locaties": [
                {
                    "UUID": str(werkingsgebied["UUID"]),
                    "Identifier": str(uuid.uuid4()),
                    "Gml_ID": str(uuid.uuid4()),
                    "Group_ID": str(uuid.uuid4()),
                    "Title": area.Source_Title,
                    "Gml": area.Gml,
                }
            ],
        }
        return result

    def _calculate_werkingsgebied_codes(self, used_objects: List[dict]) -> Set[str]:
        werkingsgebied_codes: Set[str] = set(
            [o.get("Werkingsgebied_Code") for o in used_objects if o.get("Werkingsgebied_Code", None) is not None]
        )  # type: ignore

        gebiedsaanwijzingen_codes: Set[str] = self._resolve_gebiedsaanwijzingen(used_objects)

        result = werkingsgebied_codes.union(gebiedsaanwijzingen_codes)

        return result

    def _resolve_gebiedsaanwijzingen(self, used_objects: List[dict]) -> Set[str]:
        # @todo: this implementation now looks to all fields and objects, but this is wrong
        # For example in the Programma it also used Beleidskeuze for reference, but does not use it text
        # So when a Beleidskeuze.Description has a gebiedsaanwijzing, then it will be resolved but not used
        # This needs to be updated to only check fields from types that are actually used
        values: Set[str] = set()
        pattern = r'<a[^>]*data-hint-locatie="(.*?)"[^>]*>'

        for obj in used_objects:
            for _, value in obj.items():
                if not isinstance(value, str):
                    continue

                matches = re.findall(pattern, value)
                values.update(matches)

        return values
