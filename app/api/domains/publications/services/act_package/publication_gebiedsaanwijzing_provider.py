from datetime import datetime, timezone
from uuid import uuid4
from typing import Dict, List, Set, Tuple

from pydantic import BaseModel
from bs4 import BeautifulSoup


class GebiedsaanwijzingData(BaseModel):
    uuid: str  # Used in the html so we can find this config later
    aanwijzing_type: str
    aanwijzing_group: str
    title: str
    # This is what the gebiedsaanwijzing in the html actually targets
    source_target_codes: Set[str]
    # This is all the targets resolved to gebied-codes
    gebied_codes: Set[str]
    # This is used in the GIO as for `achtergrond_actualiteit`
    # We dont really know this so we just make it now
    modified_date: datetime


class PublicationGebiedsaanwijzingProcessor:
    def __init__(self, all_objects: List[dict]):
        # Used to convert gebiedengroep-x to its used gebied-x list
        self._gebiedengroep_map: Dict[str, Set[str]] = {
            obj["Code"]: set(obj["Gebieden"])
            for obj in all_objects
            if obj.get("Object_Type") == "gebiedengroep" and isinstance(obj.get("Gebieden"), list)
        }
        self._gebiedsaanwijzingen: List[GebiedsaanwijzingData] = []

    def process(self, used_objects: List[dict]) -> Tuple[List[dict], List[GebiedsaanwijzingData]]:
        for obj_index, obj in enumerate(used_objects):
            for field_name, field_value in obj.items():
                if not isinstance(field_value, str):
                    continue

                field_value = self._resolve_gebiedsaanwijzingen(field_value)
                # We modified the contents to point to the uuid of the gebiedsaanwijzing
                # So we have to put the modified contents back into the object
                used_objects[obj_index][field_name] = field_value

        return used_objects, self._gebiedsaanwijzingen

    def _resolve_gebiedsaanwijzingen(self, html: str) -> str:
        """
        Extract gebiedengroep codes from HTML gebiedsaanwijzingen.

        HTML pattern:
            <a data-hint-type="gebiedsaanwijzing" data-aanwijzing-type="bodem" data-aanwijzing-group="bodemfunctieklasse industrie"
                data-target-codes="gebied-1,gebiedengroep-15,gebiedengroep-1" data-title="Malieveld" href="#">het Malieveld</a>
        """

        soup = BeautifulSoup(html, "html.parser")
        for aanwijzing_html in soup.select('a[data-hint-type="gebiedsaanwijzing"]'):
            aanwijzing_type: str = str(aanwijzing_html.get("data-aanwijzing-type", ""))
            aanwijzing_group: str = str(aanwijzing_html.get("data-aanwijzing-group", ""))
            aanwijzing_title: str = str(aanwijzing_html.get("data-title", ""))

            data_target_codes: Set[str] = {
                v.strip() for v in str(aanwijzing_html.get("data-target-codes", "")).split(",") if v.strip()
            }
            # We need to convert gebiedengroep-x to [gebied-x, gebied-y, ...]
            # As we can not really do anything with a gebiedengroep.
            # An gebiedengroep code does not tell me if the gebieden inside has changed (like the count of them)
            aanwijzing_gebied_codes: Set[str] = set()
            for target_code in data_target_codes:
                if target_code.startswith("gebiedengroep-"):
                    if target_code not in self._gebiedengroep_map:
                        raise RuntimeError(f"Targetted gebiedengroep `{target_code}` does not exist")
                    gebied_codes: Set[str] = self._gebiedengroep_map[target_code]
                    if len(gebied_codes) == 0:
                        raise RuntimeError(f"Used gebiedengroep `{target_code}` has no Gebieden")
                    aanwijzing_gebied_codes = aanwijzing_gebied_codes.union(gebied_codes)
                elif target_code.startswith("gebied-"):
                    aanwijzing_gebied_codes.add(target_code)
                else:
                    raise RuntimeError("Using invalid object in Gebiedengroep.Gebieden")

            aanwijzing_data: GebiedsaanwijzingData = self._resolve_data(
                aanwijzing_type,
                aanwijzing_group,
                aanwijzing_gebied_codes,
                aanwijzing_title,
                data_target_codes,
            )
            aanwijzing_html["data-hint-gebiedsaanwijzing-uuid"] = str(aanwijzing_data.uuid)
            del aanwijzing_html["data-aanwijzing-type"]
            del aanwijzing_html["data-aanwijzing-group"]
            del aanwijzing_html["data-target-codes"]
            del aanwijzing_html["data-title"]

        return str(soup)

    def _resolve_data(
        self,
        aanwijzing_type: str,
        aanwijzing_group: str,
        aanwijzing_gebied_codes: Set[str],
        title: str,
        source_target_codes: Set[str],
    ) -> GebiedsaanwijzingData:
        # Reuse if we already have a Gebiedsaanwijzing with the same data
        for aanwijzing in self._gebiedsaanwijzingen:
            if all(
                [
                    aanwijzing.aanwijzing_type == aanwijzing_type,
                    aanwijzing.aanwijzing_group == aanwijzing_group,
                    aanwijzing.gebied_codes == aanwijzing_gebied_codes,
                    aanwijzing.title == title,
                ]
            ):
                return aanwijzing

        aanwijzing = GebiedsaanwijzingData(
            uuid=str(uuid4()),
            aanwijzing_type=aanwijzing_type,
            aanwijzing_group=aanwijzing_group,
            title=title,
            gebied_codes=aanwijzing_gebied_codes,
            source_target_codes=source_target_codes,
            modified_date=datetime.now(timezone.utc),
        )
        self._gebiedsaanwijzingen.append(aanwijzing)
        return aanwijzing


class PublicationGebiedsaanwijzingProvider:
    def get_gebiedsaanwijzingen(
        self,
        all_objects: List[dict],
        used_objects: List[dict],
    ) -> Tuple[List[dict], List[GebiedsaanwijzingData]]:
        processor: PublicationGebiedsaanwijzingProcessor = PublicationGebiedsaanwijzingProcessor(all_objects)
        return processor.process(used_objects)
