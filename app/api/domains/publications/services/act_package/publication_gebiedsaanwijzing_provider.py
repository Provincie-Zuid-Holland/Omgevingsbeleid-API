from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel
from bs4 import BeautifulSoup

from app.api.domains.publications.services.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    validation_exception,
)


class GebiedsaanwijzingData(BaseModel):
    object_id: str  # Used in the frbr
    code: str
    uuid: str
    aanwijzing_type: str
    aanwijzing_group: str
    title: str
    # This is what the gebiedsaanwijzing in the html actually targets
    source_target_codes: Set[str]
    # This is all the targets resolved to gebied-codes
    resolved_gebied_codes: Set[str]
    # This is used in the GIO as for `achtergrond_actualiteit`
    achtergrond_actualiteit: str


class PublicationGebiedsaanwijzingProcessor:
    def __init__(self, all_objects: List[dict]):
        # Used to convert gebiedengroep-x to its used gebied-x list
        self._gebiedengroep_map: Dict[str, Set[str]] = {
            obj["Code"]: set(obj["Gebieden"])
            for obj in all_objects
            if obj.get("Object_Type") == "gebiedengroep" and isinstance(obj.get("Gebieden"), list)
        }

        # Lookup map to find the aanwijzing object by code
        self._gebiedsaanwijzing_map: Dict[str, dict] = {
            obj["Code"]: obj for obj in all_objects if obj.get("Object_Type") == "gebiedsaanwijzing"
        }

    def process(self, used_objects: List[dict]) -> Dict[str, GebiedsaanwijzingData]:
        # Accumulated aanwijzingen used by the text objects
        used_gebiedsaanwijzingen_codes: Set[str] = set()
        for obj in used_objects:
            object_code: str = obj["Code"]
            for field_value in obj.values():
                if not isinstance(field_value, str):
                    continue

                used_codes: Set[str] = self._find_gebiedsaanwijzingen(object_code, field_value)
                used_gebiedsaanwijzingen_codes = used_gebiedsaanwijzingen_codes.union(used_codes)

        result: Dict[str, Any] = self._resolve_data(used_gebiedsaanwijzingen_codes)
        return result

    def _find_gebiedsaanwijzingen(self, object_code: str, html: str) -> Set[str]:
        """
        Here we are searching the html for gebiedsaanwijzingen.

        <a data-hint-type="gebiedsaanwijzing" data-code="gebiedsaanwijzing-1" href="#">het Malieveld</a>
        """
        used_gebiedsaanwijzingen_codes: Set[str] = set()

        soup = BeautifulSoup(html, "html.parser")
        for aanwijzing_html in soup.select('a[data-hint-type="gebiedsaanwijzing"]'):
            aanwijzing_code: str = str(aanwijzing_html.get("data-code", ""))
            if not aanwijzing_code:
                raise validation_exception(
                    [
                        ValidatePublicationError(
                            rule="gebiedsaanwijzing_missing_attribute_data_code",
                            object=ValidatePublicationObject(code=object_code),
                            messages=[
                                f"Gebiedsaanwijzing in object `{object_code}` does not have an `data-code` attribute"
                            ],
                        )
                    ]
                )

            aanwijzing_obj: Optional[dict] = self._gebiedsaanwijzing_map.get(aanwijzing_code)
            if aanwijzing_obj is None:
                raise validation_exception(
                    [
                        ValidatePublicationError(
                            rule="gebiedsaanwijzing_invalid_code",
                            object=ValidatePublicationObject(code=object_code),
                            messages=[
                                f"Gebiedsaanwijzing in object `{object_code}` targets to Object_Code `{aanwijzing_code}` which does not exists, or is not known in publication"
                            ],
                        )
                    ]
                )

            for deprecated_attr in ["data-aanwijzing-type", "data-aanwijzing-group", "data-target-codes"]:
                for aanwijzing_attr in aanwijzing_html.attrs.keys():
                    if deprecated_attr == aanwijzing_attr:
                        raise validation_exception(
                            [
                                ValidatePublicationError(
                                    rule="gebiedsaanwijzing_html_deprecated_attribute",
                                    object=ValidatePublicationObject(code=object_code),
                                    messages=[
                                        f"Gebiedsaanwijzing in object `{object_code}` uses deprecated attribute `{deprecated_attr}` in HTML"
                                    ],
                                )
                            ]
                        )

            used_gebiedsaanwijzingen_codes.add(aanwijzing_code)

        return used_gebiedsaanwijzingen_codes

    def _resolve_data(
        self,
        aanwijzing_codes: Set[str],
    ) -> Dict[str, GebiedsaanwijzingData]:
        result: Dict[str, GebiedsaanwijzingData] = {}

        for aanwijzing_code in aanwijzing_codes:
            aanwijzing_obj: Optional[dict] = self._gebiedsaanwijzing_map.get(aanwijzing_code)
            if aanwijzing_obj is None:
                # This should never be triggered and has already been raised previously before when the object code that uses this was identified
                raise validation_exception(
                    [
                        ValidatePublicationError(
                            rule="gebiedsaanwijzing_unknown_code",
                            object=ValidatePublicationObject(),
                            messages=[f"Unknown gebiedsaanwijzing code `{aanwijzing_code}`"],
                        )
                    ]
                )

            source_target_codes: Set[str] = set(aanwijzing_obj["Target_Codes"])
            gebied_codes: Set[str] = self._resolve_gebied_codes(aanwijzing_code, source_target_codes)

            # We transform it to a plain dict, because the state system can then freely use it
            aanwijzing = GebiedsaanwijzingData(
                object_id=str(aanwijzing_obj["Object_ID"]),
                code=str(aanwijzing_obj["Code"]),
                uuid=str(aanwijzing_obj["UUID"]),
                aanwijzing_type=str(aanwijzing_obj["Ref_Type"]),
                aanwijzing_group=str(aanwijzing_obj["Ref_Group"]),
                title=str(aanwijzing_obj["Title"]),
                source_target_codes=source_target_codes,
                resolved_gebied_codes=gebied_codes,
                achtergrond_actualiteit=str(datetime.now(timezone.utc))[:10],
            )

            result[aanwijzing_code] = aanwijzing

        return result

    def _resolve_gebied_codes(self, aanwijzing_code: str, target_codes: Set[str]) -> Set[str]:
        """
        Resolved the target codes to gebied codes.
        As the target code can be a gebiedengroep.

        Example:
            input ['gebiedengroep-1', 'gebied-5']
            output ['gebied-1', 'gebied-2', 'gebied-5']

            if gebiedengroep-1 has the following gebieden: ['gebied-1', 'gebied-2']
        """
        result: Set[str] = set()

        for target_code in target_codes:
            if target_code.startswith("gebiedengroep-"):
                if target_code not in self._gebiedengroep_map:
                    raise validation_exception(
                        [
                            ValidatePublicationError(
                                rule="gebiedsaanwijzing_gebiedengroep_not_found",
                                object=ValidatePublicationObject(code=aanwijzing_code),
                                messages=[f"Targeted gebiedengroep `{target_code}` does not exist"],
                            )
                        ]
                    )
                gebied_codes: Set[str] = self._gebiedengroep_map[target_code]
                if len(gebied_codes) == 0:
                    raise validation_exception(
                        [
                            ValidatePublicationError(
                                rule="gebiedsaanwijzing_no_targets",
                                object=ValidatePublicationObject(code=aanwijzing_code),
                                messages=[f"Used gebiedengroep `{target_code}` has no Gebieden"],
                            )
                        ]
                    )
                result = result.union(gebied_codes)

            elif target_code.startswith("gebied-"):
                result.add(target_code)
            else:
                raise validation_exception(
                    [
                        ValidatePublicationError(
                            rule="gebiedsaanwijzing_invalid_target",
                            object=ValidatePublicationObject(code=aanwijzing_code),
                            messages=["Using invalid object in gebiedsaanwijzing.Target_Codes"],
                        )
                    ]
                )

        return result


class PublicationGebiedsaanwijzingProvider:
    def get_gebiedsaanwijzingen(
        self,
        all_objects: List[dict],
        used_objects: List[dict],
    ) -> Dict[str, GebiedsaanwijzingData]:
        processor: PublicationGebiedsaanwijzingProcessor = PublicationGebiedsaanwijzingProcessor(all_objects)
        return processor.process(used_objects)
