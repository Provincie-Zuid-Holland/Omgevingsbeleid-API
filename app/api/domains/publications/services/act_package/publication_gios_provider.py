import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional


from app.api.domains.publications.services.act_package.publication_gebieden_provider import (
    GebiedenData,
    InputGebied,
    InputGebiedengroep,
)
from app.api.domains.publications.services.act_package.publication_gebiedsaanwijzing_provider import (
    GebiedsaanwijzingData,
)
import dso.models as dso_models
from sqlalchemy.orm import Session

from app.api.domains.publications.services.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    validation_exception,
)
from app.api.domains.publications.types.api_input_data import (
    ActFrbr,
    PublicationGebiedengroep,
    PublicationGebiedsaanwijzing,
    PublicationGeoData,
    PublicationGio,
    PublicationGioLocatie,
)
from app.api.domains.werkingsgebieden.repositories.area_repository import AreaRepository
from app.core.tables.others import AreasTable


class PublicationGiosProvider:
    def __init__(self, session: Session, area_repository: AreaRepository, act_frbr: ActFrbr):
        self._session: Session = session
        self._area_repository: AreaRepository = area_repository
        self._act_frbr: ActFrbr = act_frbr
        self._result: PublicationGeoData = PublicationGeoData()

    def resolve_geo(
        self,
        gebieden_data: GebiedenData,
        gebiedsaanwijzingen: Dict[str, GebiedsaanwijzingData],
    ) -> PublicationGeoData:
        self._resolve_gebiedengroepen(gebieden_data)
        self._resolve_gebiedsaanwijzingen(gebieden_data, gebiedsaanwijzingen)

        return self._result

    #
    # Gebiedengroepen
    #

    def _resolve_gebiedengroepen(self, gebieden_data: GebiedenData):
        for input_groep in gebieden_data.used_gebiedengroepen:
            # We build a GIO for each gebiedengroep
            locations: List[PublicationGioLocatie] = []
            for gebied_code in input_groep.gebied_codes:
                input_gebied: InputGebied = self._find_input_gebied(gebieden_data, gebied_code, input_groep.code)
                location: PublicationGioLocatie = self._as_location(input_gebied)
                locations.append(location)

            gio: PublicationGio = PublicationGio(
                key=input_groep.code,
                source_codes=input_groep.gebied_codes,
                title=input_groep.title,
                frbr=self._build_frbr_gebiedengroep(input_groep),
                new=True,
                geboorteregeling=self._act_frbr.get_work(),
                achtergrond_verwijzing="TOP10NL",
                achtergrond_actualiteit=str(input_groep.modified_date)[:10],
                locaties=locations,
            )
            # Save to accumulator
            self._result.gios[gio.key] = gio

            groep: PublicationGebiedengroep = PublicationGebiedengroep(
                uuid=str(input_groep.uuid),
                code=input_groep.code,
                title=input_groep.title,
                source_gebieden_codes=input_groep.gebied_codes,
                gio_key=gio.key,
            )
            # Save to accumulator
            self._result.gebiedengroepen[groep.code] = groep

    def _build_frbr_gebiedengroep(self, input_gebiedengroep: InputGebiedengroep) -> dso_models.GioFRBR:
        # Note: GIO's are consolidated per Act, so we use the Act's Work_Date
        # and make their identifier unique with act data.
        # Can't really remember why, but I think it's a legacy system in DSO where the same FRBR must be unique (Omgevingsvisie/programma should not use the same)
        # I added GG as a shorthand for Gebiedengroep
        work_date: str = self._act_frbr.Work_Date
        work_identifier = (
            f"{self._act_frbr.Act_ID}-{self._act_frbr.Expression_Version}-GG-{input_gebiedengroep.object_id}"
        )
        return dso_models.GioFRBR(
            Work_Province_ID=self._act_frbr.Work_Province_ID,
            Work_Date=work_date,
            Work_Other=work_identifier,
            Expression_Language=self._act_frbr.Expression_Language,
            Expression_Date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            Expression_Version=1,
        )

    #
    # Gebiedsaanwijzingen
    #

    def _resolve_gebiedsaanwijzingen(
        self, gebieden_data: GebiedenData, gebiedsaanwijzingen: Dict[str, GebiedsaanwijzingData]
    ):
        for input_aanwijzing in gebiedsaanwijzingen.values():
            # We build a GIO for each gebiedsaanwijzing
            locations: List[PublicationGioLocatie] = []
            for gebied_code in input_aanwijzing.resolved_gebied_codes:
                input_gebied: InputGebied = self._find_input_gebied(gebieden_data, gebied_code, input_aanwijzing.code)
                location: PublicationGioLocatie = self._as_location(input_gebied)
                locations.append(location)

            gio: PublicationGio = PublicationGio(
                key=input_aanwijzing.code,
                source_codes=input_aanwijzing.resolved_gebied_codes,
                title=input_aanwijzing.title,
                frbr=self._build_frbr_gebiedsaanwijzing(input_aanwijzing),
                new=True,
                geboorteregeling=self._act_frbr.get_work(),
                achtergrond_verwijzing="TOP10NL",
                achtergrond_actualiteit=input_aanwijzing.achtergrond_actualiteit,
                locaties=locations,
            )
            # Save to accumulator
            self._result.gios[gio.key] = gio

            aanwijzing: PublicationGebiedsaanwijzing = PublicationGebiedsaanwijzing(
                uuid=str(input_aanwijzing.uuid),
                code=input_aanwijzing.code,
                title=input_aanwijzing.title,
                aanwijzing_type=input_aanwijzing.aanwijzing_type,
                aanwijzing_group=input_aanwijzing.aanwijzing_group,
                gio_key=gio.key,
                source_target_codes=input_aanwijzing.source_target_codes,
                resolved_gebied_codes=input_aanwijzing.resolved_gebied_codes,
            )
            # Save to accumulator
            self._result.gebiedsaanwijzingen[aanwijzing.code] = aanwijzing

    def _build_frbr_gebiedsaanwijzing(self, input_aanwijzing: GebiedsaanwijzingData) -> dso_models.GioFRBR:
        # Note: GIO's are consolidated per Act, so we use the Act's Work_Date
        # and make their identifier unique with act data.
        # Can't really remember why, but I think it's a legacy system in DSO where the same FRBR must be unique (Omgevingsvisie/programma should not use the same)
        # I added GA as a shorthand for Gebiedsaanwijzing
        work_date: str = self._act_frbr.Work_Date
        work_identifier = f"{self._act_frbr.Act_ID}-{self._act_frbr.Expression_Version}-GA-{input_aanwijzing.object_id}"
        return dso_models.GioFRBR(
            Work_Province_ID=self._act_frbr.Work_Province_ID,
            Work_Date=work_date,
            Work_Other=work_identifier,
            Expression_Language=self._act_frbr.Expression_Language,
            Expression_Date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            Expression_Version=1,
        )

    #
    # Helpers
    #

    def _find_input_gebied(self, gebieden_data: GebiedenData, gebied_code: str, parent_code: str) -> InputGebied:
        gebied: Optional[InputGebied] = gebieden_data.all_gebieden.get(gebied_code)
        if gebied is None:
            raise validation_exception(
                [
                    ValidatePublicationError(
                        rule="gebied_not_found",
                        object=ValidatePublicationObject(code=parent_code),
                        messages=[f"Searching for gebied `{gebied_code}` which was not loaded"],
                    )
                ]
            )
        return gebied

    def _fetch_area(self, input_gebied: InputGebied) -> AreasTable:
        area: Optional[AreasTable] = self._area_repository.get_with_gml(self._session, input_gebied.area_uuid)
        if area is None:
            raise validation_exception(
                [
                    ValidatePublicationError(
                        rule="area_not_found",
                        object=ValidatePublicationObject(code=input_gebied.code),
                        messages=[f"Area UUID {input_gebied.area_uuid} does not exist"],
                    )
                ]
            )
        return area

    def _as_location(self, input_gebied: InputGebied) -> PublicationGioLocatie:
        area: AreasTable = self._fetch_area(input_gebied)
        gml_hash = hashlib.sha512()
        gml_hash.update(area.Gml.encode())

        return PublicationGioLocatie(
            code=input_gebied.code,
            title=input_gebied.title,
            basisgeo_id=str(input_gebied.basisgeo_id),
            source_hash=gml_hash.hexdigest(),
            gml=area.Gml,
        )


class PublicationGiosProviderFactory:
    def __init__(self, area_repository: AreaRepository):
        self._area_repository: AreaRepository = area_repository

    def process(
        self,
        session: Session,
        act_frbr: ActFrbr,
        gebieden_data: GebiedenData,
        gebiedsaanwijzingen: Dict[str, GebiedsaanwijzingData],
    ) -> PublicationGeoData:
        service: PublicationGiosProvider = PublicationGiosProvider(
            session,
            self._area_repository,
            act_frbr,
        )
        return service.resolve_geo(gebieden_data, gebiedsaanwijzingen)
