import hashlib
from re import M
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field

from app.api.domains.publications.services.act_package.publication_gebiedsaanwijzing_provider import (
    GebiedsaanwijzingData,
)
import dso.models as dso_models
from sqlalchemy.orm import Session

from app.api.domains.publications.types.api_input_data import ActFrbr
from app.api.domains.werkingsgebieden.repositories.area_repository import AreaRepository
from app.core.tables.others import AreasTable


class InputGebied(BaseModel):
    uuid: UUID
    code: str
    area_uuid: UUID
    # We overwrite this with the area.Title at the moment
    # But I think we should use the objects title instead as we can modify it
    # @todo: need to do research if we can change the title of a GIO
    title: str
    # These are used in the FRBR
    modified_date: datetime
    object_id: int

    # "uuid": gebied["UUID"],
    # "code": gebied["Code"],
    # "identifier": str(uuid.uuid4()),
    # "new": True,  # Will be updated by state system if existing
    # "title": area.Source_Title,
    # "frbr": frbr,
    # "geboorteregeling": act_frbr.get_work(),
    # "achtergrond_verwijzing": "TOP10NL",
    # "achtergrond_actualiteit": str(gebied["Modified_Date"])[:10],
    # "gml_id": str(uuid.uuid4()),
    # "gml": area.Gml,
    # "hash": gml_hash,


class InputGebiedengroep(BaseModel):
    uuid: UUID
    object_id: int
    code: str
    # We do use this title for ow.gebiedengroep
    # See how weird it is that we dont use the Gebied.Title
    title: str
    gebied_codes: Set[str]
    # "uuid": gebiedengroep["UUID"],
    # "identifier": str(uuid.uuid4()),
    # "code": gebiedengroep["Code"],
    # "title": gebiedengroep["Title"],
    # "area_codes": gebieden_codes,


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
        used_gebied_objects: List[InputGebied] = [
            g for g in all_gebied_objects.values()
            if g.code in used_gebied_codes
        ]

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
        gebied_objects: List[dict] = [
            o for o in all_objects if o["Object_Type"] == "gebied"
        ]

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

    # def _as_dso_gebied(
    #     self,
    #     act_frbr: ActFrbr,
    #     gebied: dict,
    #     area: AreasTable,
    # ) -> dict:
    #     """
    #     Transform gebied object to DSO Gebied format.

    #     This matches the structure expected by:
    #     dso.act_builder.state_manager.input_data.resource.gebieden.types.Gebied

    #     Note: Gebieden are consolidated per Act, so we use the Act's Work_Date
    #     and make their identifier unique with act data.
    #     """
    #     work_date: str = act_frbr.Work_Date
    #     work_identifier = f"{act_frbr.Act_ID}-{act_frbr.Expression_Version}-{gebied['Object_ID']}"

    #     # Create GIO FRBR
    #     # Expression values are set as if this is the first version
    #     # They will be overwritten by the state system if already published
    #     frbr = dso_models.GioFRBR(
    #         Work_Province_ID=act_frbr.Work_Province_ID,
    #         Work_Date=work_date,
    #         Work_Other=work_identifier,
    #         Expression_Language=act_frbr.Expression_Language,
    #         Expression_Date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    #         Expression_Version=1,
    #     )

    #     gml_hash = hashlib.sha512()
    #     gml_hash.update(area.Gml.encode())

    #     result = {
    #         "uuid": gebied["UUID"],
    #         "code": gebied["Code"],
    #         "identifier": str(uuid4()),
    #         "new": True,  # Will be updated by state system if existing
    #         "title": area.Source_Title,
    #         "frbr": frbr,
    #         "geboorteregeling": act_frbr.get_work(),
    #         "achtergrond_verwijzing": "TOP10NL",
    #         "achtergrond_actualiteit": str(gebied["Modified_Date"])[:10],
    #         "gml_id": str(uuid4()),
    #         "gml": area.Gml,
    #         "hash": gml_hash,
    #     }
    #     return result

    # def _transform_gebiedengroepen(
    #     self,
    #     gebiedengroep_objects: List[dict],
    # ) -> List[dict]:
    #     result: List[dict] = []
    #     for groep in gebiedengroep_objects:
    #         dso_groep = self._as_dso_gebiedengroep(groep)
    #         result.append(dso_groep)

    #     return result

    # def _as_dso_gebiedengroep(
    #     self,
    #     gebiedengroep: dict,
    # ) -> dict:
    #     """
    #     Transform gebiedengroep object to DSO GebiedenGroep format.

    #     This matches the structure expected by:
    #     dso.act_builder.state_manager.input_data.resource.gebieden.types.GebiedenGroep
    #     """
    #     gebieden_codes: List[str] = gebiedengroep["Gebieden"]

    #     result = {
    #         "uuid": gebiedengroep["UUID"],
    #         "identifier": str(uuid4()),
    #         "code": gebiedengroep["Code"],
    #         "title": gebiedengroep["Title"],
    #         "area_codes": gebieden_codes,
    #     }
    #     return result
