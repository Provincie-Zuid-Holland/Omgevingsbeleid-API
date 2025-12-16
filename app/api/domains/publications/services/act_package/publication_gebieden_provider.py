from uuid import UUID
from datetime import datetime
from typing import Dict, List, Optional, Set

from pydantic import BaseModel


class InputGebied(BaseModel):
    # Represents an Object_Type=gebied and which convert to a DSO.GioLocatie
    uuid: UUID
    object_id: int
    code: str
    area_uuid: UUID
    # We overwrite this with the area.Title at the moment
    # But I think we should use the objects title instead as we can modify it
    # @todo: need to do research if we can change the title of a GIO
    title: str
    # These are used in the FRBR
    modified_date: datetime


class InputGebiedengroep(BaseModel):
    uuid: UUID
    object_id: int
    code: str
    # We do use this title for ow.gebiedengroep
    # See how weird it is that we dont use the Gebied.Title
    title: str
    gebied_codes: Set[str]


class GebiedenData(BaseModel):
    # This is dragged along for Gebiedsaanwijzing
    # which might point to non used Gebieden
    all_gebieden: Dict[str, InputGebied]
    used_gebieden: List[InputGebied]
    used_gebiedengroepen: List[InputGebiedengroep]


class PublicationGebiedenProvider:
    def get_gebieden_data(
        self,
        all_objects: List[dict],
        used_objects: List[dict],
    ) -> GebiedenData:
        used_gebiedengroep_objects: List[InputGebiedengroep] = self._get_gebiedengroep_objects(
            all_objects,
            used_objects,
        )
        used_gebied_codes: Set[str] = self._extract_gebied_codes(used_gebiedengroep_objects)
        all_gebied_objects: Dict[str, InputGebied] = self._get_gebied_objects(all_objects)
        used_gebied_objects: List[InputGebied] = [g for g in all_gebied_objects.values() if g.code in used_gebied_codes]

        return GebiedenData(
            all_gebieden=all_gebied_objects,
            used_gebieden=used_gebied_objects,
            used_gebiedengroepen=used_gebiedengroep_objects,
        )

    def _get_gebiedengroep_objects(
        self,
        all_objects: List[dict],
        used_objects: List[dict],
    ) -> List[InputGebiedengroep]:
        gebiedengroep_codes: Set[str] = self._calculate_gebiedengroep_codes(used_objects)
        groep_objects: List[dict] = [o for o in all_objects if o["Object_Type"] == "gebiedengroep"]
        used_groep_objects: List[InputGebiedengroep] = [
            InputGebiedengroep(
                uuid=g["UUID"],
                object_id=g["Object_ID"],
                code=g["Code"],
                title=g["Title"],
                gebied_codes=set(g["Gebieden"] or []),
            )
            for g in groep_objects
            if g["Code"] in gebiedengroep_codes
        ]
        return used_groep_objects

    def _calculate_gebiedengroep_codes(self, used_objects: List[dict]) -> Set[str]:
        used_codes: Set[str] = set(
            [o.get("Gebiedengroep_Code") for o in used_objects if o.get("Gebiedengroep_Code", None) is not None]
        )  # type: ignore
        return used_codes

    def _extract_gebied_codes(
        self,
        gebiedengroep_objects: List[InputGebiedengroep],
    ) -> Set[str]:
        gebied_codes: Set[str] = set()
        for groep in gebiedengroep_objects:
            gebied_codes.update(groep.gebied_codes)
        return gebied_codes

    def _get_gebied_objects(self, all_objects: List[dict]) -> Dict[str, InputGebied]:
        gebied_objects: List[dict] = [o for o in all_objects if o["Object_Type"] == "gebied"]

        result: Dict[str, InputGebied] = {}
        for gebied in gebied_objects:
            code: str = gebied["Code"]
            area_uuid: Optional[str] = gebied.get("Area_UUID")
            if area_uuid is None:
                raise RuntimeError(f"Missing Area_UUID for gebied with code: {code}")

            input_gebied: InputGebied = InputGebied(
                uuid=gebied["UUID"],
                object_id=gebied["Object_ID"],
                code=code,
                area_uuid=area_uuid,
                title=gebied["Title"],
                modified_date=gebied["Modified_Date"],
            )
            result[code] = input_gebied

        return result
