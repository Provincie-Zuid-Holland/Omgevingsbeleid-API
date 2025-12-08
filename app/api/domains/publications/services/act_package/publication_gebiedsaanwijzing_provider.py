from uuid import uuid4
from typing import List, Set, Tuple

from pydantic import BaseModel, Field
from bs4 import BeautifulSoup


class GebiedsaanwijzingData(BaseModel):
    uuid: str
    # `ow_identifier` This is used for the OW registration
    # And this is deliberately another UUID
    # So we might store these objects as the UUID in our database at some point
    # And not have conflicts that we cant change the `ow_identifier`
    # All in all its way saver to store them separately
    ow_identifier: str
    aanwijzing_type: str
    aanwijzing_group: str
    title: str
    target_codes: Set[str] = Field(default_factory=set)

    def get_gebiedengroep_codes(self) -> Set[str]:
        return {code for code in self.target_codes if code.startswith("gebiedengroep-")}

    def get_gebieden_codes(self) -> Set[str]:
        return {code for code in self.target_codes if code.startswith("gebied-")}


class PublicationGebiedsaanwijzingProcessor:
    def __init__(self):
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
            <a data-type="gebiedsaanwijzing" data-aanwijzing-type="water" data-aanwijzing-group="bodem"
                data-target-codes="gebied-1 gebiedengroep-15 gebiedengroep-1" href="#">Malieveld</a>
        """

        soup = BeautifulSoup(html, "html.parser")
        for aanwijzing_html in soup.select('a[data-type="gebiedsaanwijzing"]'):
            aanwijzing_type: str = str(aanwijzing_html.get("data-aanwijzing-type", ""))
            aanwijzing_group: str = str(aanwijzing_html.get("data-aanwijzing-group", ""))
            aanwijzing_target_codes: Set[str] = set(str(aanwijzing_html.get("data-target_codes", "")).split(" "))
            aanwijzing_title: str = aanwijzing_html.get_text(strip=True)

            aanwijzing_data: GebiedsaanwijzingData = self._resolve_data(
                aanwijzing_type,
                aanwijzing_group,
                aanwijzing_target_codes,
                aanwijzing_title,
            )
            aanwijzing_html["data-gebiedsaanwijzing-uuid"] = str(aanwijzing_data.uuid)

        return str(soup)

    def _resolve_data(
        self,
        aanwijzing_type: str,
        aanwijzing_group: str,
        aanwijzing_target_codes: Set[str],
        aanwijzing_title: str,
    ) -> GebiedsaanwijzingData:
        # Reuse if we already have a Gebiedsaanwijzing with the same data
        for aanwijzing in self._gebiedsaanwijzingen:
            if all(
                [
                    aanwijzing.aanwijzing_type == aanwijzing_type,
                    aanwijzing.aanwijzing_group == aanwijzing_group,
                    aanwijzing.target_codes == aanwijzing_target_codes,
                    aanwijzing.title == aanwijzing_title,
                ]
            ):
                return aanwijzing

        aanwijzing = GebiedsaanwijzingData(
            uuid=str(uuid4()),
            ow_identifier=str(uuid4()),
            aanwijzing_type=aanwijzing_type,
            aanwijzing_group=aanwijzing_group,
            title=aanwijzing_title,
            target_codes=aanwijzing_target_codes,
        )
        self._gebiedsaanwijzingen.append(aanwijzing)
        return aanwijzing


class PublicationGebiedsaanwijzingProvider:
    def get_gebiedsaanwijzingen(
        self,
        used_objects: List[dict],
    ) -> Tuple[List[dict], List[GebiedsaanwijzingData]]:
        processor: PublicationGebiedsaanwijzingProcessor = PublicationGebiedsaanwijzingProcessor()
        return processor.process(used_objects)
