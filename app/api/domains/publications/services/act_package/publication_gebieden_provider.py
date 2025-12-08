import hashlib
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Set

from pydantic import BaseModel, Field

from app.api.domains.publications.services.act_package.publication_gebiedsaanwijzing_provider import (
    GebiedsaanwijzingData,
)
import dso.models as dso_models
from sqlalchemy.orm import Session

from app.api.domains.publications.types.api_input_data import ActFrbr
from app.api.domains.werkingsgebieden.repositories.area_repository import AreaRepository
from app.core.tables.others import AreasTable


class GebiedenData(BaseModel):
    gebieden: List[dict] = Field(default_factory=list)
    gebiedengroepen: List[dict] = Field(default_factory=list)


class PublicationGebiedenProvider:
    def __init__(self, area_repository: AreaRepository):
        self._area_repository: AreaRepository = area_repository

    def get_gebieden_data(
        self,
        session: Session,
        act_frbr: ActFrbr,
        all_objects: List[dict],
        used_objects: List[dict],
        gebiedsaanwijzingen: List[GebiedsaanwijzingData],
        all_data: bool = False,
    ) -> GebiedenData:
        gebiedengroep_codes: Set[str] = self._calculate_gebiedengroep_codes(
            used_objects,
            gebiedsaanwijzingen,
        )
        used_gebiedengroep_objects: List[dict] = self._filter_gebiedengroep_objects(
            all_objects,
            gebiedengroep_codes,
            all_data,
        )

        gebied_codes: Set[str] = self._extract_gebied_codes_from_groepen(
            used_gebiedengroep_objects,
            gebiedsaanwijzingen,
        )
        gebieden: List[dict] = self._get_gebieden_with_areas(
            session,
            act_frbr,
            all_objects,
            gebied_codes,
        )

        gebiedengroepen: List[dict] = self._transform_gebiedengroepen(used_gebiedengroep_objects)

        return GebiedenData(
            gebieden=gebieden,
            gebiedengroepen=gebiedengroepen,
        )

    def _calculate_gebiedengroep_codes(
        self, used_objects: List[dict], gebiedsaanwijzingen: List[GebiedsaanwijzingData]
    ) -> Set[str]:
        direct_codes: Set[str] = set(
            [o.get("Gebiedengroep_Code") for o in used_objects if o.get("Gebiedengroep_Code", None) is not None]
        )  # type: ignore

        codes_from_gebiedsaanwijzing: Set[str] = {
            code for gebiedsaanwijzing in gebiedsaanwijzingen for code in gebiedsaanwijzing.get_gebiedengroep_codes()
        }

        return direct_codes.union(codes_from_gebiedsaanwijzing)

    def _filter_gebiedengroep_objects(
        self,
        all_objects: List[dict],
        used_codes: Set[str],
        all_data: bool,
    ) -> List[dict]:
        groep_objects: List[dict] = [o for o in all_objects if o["Object_Type"] == "gebiedengroep"]

        if all_data:
            return groep_objects
        # Otherwise, filter to only used codes
        return [g for g in groep_objects if g["Code"] in used_codes]

    def _extract_gebied_codes_from_groepen(
        self,
        gebiedengroep_objects: List[dict],
        gebiedsaanwijzingen: List[GebiedsaanwijzingData],
    ) -> Set[str]:
        gebied_codes: Set[str] = set()
        for groep in gebiedengroep_objects:
            gebieden_list: List[str] = groep.get("Gebieden", [])
            if not isinstance(gebieden_list, list):
                continue

            gebied_codes.update(gebieden_list)

        codes_from_gebiedsaanwijzing: Set[str] = {
            code for gebiedsaanwijzing in gebiedsaanwijzingen for code in gebiedsaanwijzing.get_gebieden_codes()
        }

        return gebied_codes.union(codes_from_gebiedsaanwijzing)

    def _get_gebieden_with_areas(
        self,
        session: Session,
        act_frbr: ActFrbr,
        all_objects: List[dict],
        gebied_codes: Set[str],
    ) -> List[dict]:
        gebied_objects: List[dict] = [
            o for o in all_objects if o["Object_Type"] == "gebied" and o["Code"] in gebied_codes
        ]

        result: List[dict] = []
        for gebied in gebied_objects:
            code: str = gebied["Code"]
            area_uuid: Optional[str] = gebied.get("Area_UUID")
            if area_uuid is None:
                raise RuntimeError(f"Missing Area_UUID for gebied with code: {code}")

            area: Optional[AreasTable] = self._area_repository.get_with_gml(session, area_uuid)
            if area is None:
                raise RuntimeError(f"Area UUID {area_uuid} does not exist for gebied code: {code}")

            dso_gebied: dict = self._as_dso_gebied(act_frbr, gebied, area)
            result.append(dso_gebied)

        return result

    def _as_dso_gebied(
        self,
        act_frbr: ActFrbr,
        gebied: dict,
        area: AreasTable,
    ) -> dict:
        """
        Transform gebied object to DSO Gebied format.

        This matches the structure expected by:
        dso.act_builder.state_manager.input_data.resource.gebieden.types.Gebied

        Note: Gebieden are consolidated per Act, so we use the Act's Work_Date
        and make their identifier unique with act data.
        """
        work_date: str = act_frbr.Work_Date
        work_identifier = f"{act_frbr.Act_ID}-{act_frbr.Expression_Version}-{gebied['Object_ID']}"

        # Create GIO FRBR
        # Expression values are set as if this is the first version
        # They will be overwritten by the state system if already published
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
            "uuid": gebied["UUID"],
            "code": gebied["Code"],
            "identifier": str(uuid.uuid4()),
            "new": True,  # Will be updated by state system if existing
            "title": area.Source_Title,
            "frbr": frbr,
            "geboorteregeling": act_frbr.get_work(),
            "achtergrond_verwijzing": "TOP10NL",
            "achtergrond_actualiteit": str(gebied["Modified_Date"])[:10],
            "gml_id": str(uuid.uuid4()),
            "gml": area.Gml,
            "hash": gml_hash,
        }
        return result

    def _transform_gebiedengroepen(
        self,
        gebiedengroep_objects: List[dict],
    ) -> List[dict]:
        result: List[dict] = []
        for groep in gebiedengroep_objects:
            dso_groep = self._as_dso_gebiedengroep(groep)
            result.append(dso_groep)

        return result

    def _as_dso_gebiedengroep(
        self,
        gebiedengroep: dict,
    ) -> dict:
        """
        Transform gebiedengroep object to DSO GebiedenGroep format.

        This matches the structure expected by:
        dso.act_builder.state_manager.input_data.resource.gebieden.types.GebiedenGroep
        """
        gebieden_codes: List[str] = gebiedengroep["Gebieden"]

        result = {
            "uuid": gebiedengroep["UUID"],
            "identifier": str(uuid.uuid4()),
            "code": gebiedengroep["Code"],
            "title": gebiedengroep["Title"],
            "area_codes": gebieden_codes,
        }
        return result
