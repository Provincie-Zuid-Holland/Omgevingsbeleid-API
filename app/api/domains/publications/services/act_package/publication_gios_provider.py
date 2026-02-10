import hashlib
from uuid import UUID
from datetime import datetime, timezone
from typing import List, Optional, Set


from app.api.domains.publications.services.act_package.publication_gebieden_provider import GebiedenData, InputGebied
from app.api.domains.publications.services.act_package.publication_gebiedsaanwijzing_provider import (
    GebiedsaanwijzingData,
)
import dso.models as dso_models
from sqlalchemy.orm import Session

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
        gebiedsaanwijzingen: List[GebiedsaanwijzingData],
    ) -> PublicationGeoData:
        self._resolve_gebiedengroepen(gebieden_data)
        self._resolve_gebiedsaanwijzingen(gebieden_data, gebiedsaanwijzingen)

        return self._result

    def _resolve_gebiedengroepen(self, gebieden_data: GebiedenData):
        for input_groep in gebieden_data.used_gebiedengroepen:
            # For gebiedengroepen, we put each gebied in its own gio
            gio_keys: Set[str] = set()
            for gebied_code in input_groep.gebied_codes:
                input_gebied: InputGebied = self._find_input_gebied(gebieden_data, gebied_code)
                gio: PublicationGio = self._resolve_gio_from_gebied(input_gebied)
                gio_keys.add(gio.key())

            groep: PublicationGebiedengroep = PublicationGebiedengroep(
                uuid=str(input_groep.uuid),
                code=input_groep.code,
                title=input_groep.title,
                source_gebieden_codes=input_groep.gebied_codes,
                gio_keys=gio_keys,
            )
            # Save to accumulator
            self._result.gebiedengroepen[groep.key()] = groep

    def _find_input_gebied(self, gebieden_data: GebiedenData, code: str) -> InputGebied:
        for gebied in gebieden_data.used_gebieden:
            if gebied.code == code:
                return gebied

        raise RuntimeError(f"Searching for gebied `{code}` which was not loaded")

    def _resolve_gebiedsaanwijzingen(
        self,
        gebieden_data: GebiedenData,
        gebiedsaanwijzingen: List[GebiedsaanwijzingData],
    ):
        for input_aanwijzing in gebiedsaanwijzingen:
            # For gebiedsaanwijzing we must build 1 gio that has all the gebieden
            gio: PublicationGio = self._resolve_gio_for_aanwijzing(gebieden_data, input_aanwijzing)
            aanwijzing: PublicationGebiedsaanwijzing = PublicationGebiedsaanwijzing(
                uuid=input_aanwijzing.uuid,
                aanwijzing_type=input_aanwijzing.aanwijzing_type,
                aanwijzing_group=input_aanwijzing.aanwijzing_group,
                title=input_aanwijzing.title,
                source_target_codes=input_aanwijzing.source_target_codes,
                source_gebied_codes=input_aanwijzing.gebied_codes,
                gio_key=gio.key(),
            )
            # Save to accumulator
            self._result.gebiedsaanwijzingen[aanwijzing.key()] = aanwijzing

    def _inputgebied_to_gio(self, input_gebied: InputGebied, area: AreasTable) -> PublicationGio:
        locatie: PublicationGioLocatie = self._area_to_locatie(area, input_gebied)

        gio: PublicationGio = PublicationGio(
            source_codes=set([input_gebied.code]),
            title=input_gebied.title,
            frbr=self._build_frbr_gebied(input_gebied),
            new=True,
            geboorteregeling=self._act_frbr.get_work(),
            achtergrond_verwijzing="TOP10NL",
            achtergrond_actualiteit=str(input_gebied.modified_date)[:10],
            locaties=[locatie],
        )

        # Save to accumulator
        self._result.gios[gio.key()] = gio

        return gio

    def _build_frbr_gebied(self, input_gebied: InputGebied) -> dso_models.GioFRBR:
        # Note: Gebieden are consolidated per Act, so we use the Act's Work_Date
        # and make their identifier unique with act data.
        work_date: str = self._act_frbr.Work_Date
        work_identifier = f"{self._act_frbr.Act_ID}-{self._act_frbr.Expression_Version}-{input_gebied.object_id}"
        return dso_models.GioFRBR(
            Work_Province_ID=self._act_frbr.Work_Province_ID,
            Work_Date=work_date,
            Work_Other=work_identifier,
            Expression_Language=self._act_frbr.Expression_Language,
            Expression_Date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            Expression_Version=1,
        )

    def _resolve_gio_from_gebied(self, input_gebied: InputGebied) -> PublicationGio:
        area: AreasTable = self._fetch_area(input_gebied.area_uuid)
        gio: PublicationGio = self._inputgebied_to_gio(input_gebied, area)
        return gio

    def _resolve_gio_for_aanwijzing(
        self, gebieden_data: GebiedenData, input_aanwijzing: GebiedsaanwijzingData
    ) -> PublicationGio:
        # It could be that we have this Gio already because the `Gebiedengroep` made it
        # or another `Gebiedsaanwijzing` made it
        gio_key: str = "_".join(sorted(input_aanwijzing.gebied_codes))
        existing_gio: Optional[PublicationGio] = self._result.gios.get(gio_key)
        if existing_gio is not None:
            return existing_gio

        # Make the GIO based on all gebied codes in the input_aanwijzing.
        # Note that these might not exists in the "used_" selection.
        # So we need to dig into GebiedenData.all_gebieden
        locaties: List[PublicationGioLocatie] = []
        for gebied_code in input_aanwijzing.gebied_codes:
            input_gebied: Optional[InputGebied] = gebieden_data.all_gebieden.get(gebied_code)
            if input_gebied is None:
                raise RuntimeError(
                    f"Gebiedsaanwijzijng `{input_aanwijzing.title}` points to unknown gebied `{gebied_code}`"
                )
            area: AreasTable = self._fetch_area(input_gebied.area_uuid)
            locatie: PublicationGioLocatie = self._area_to_locatie(area, input_gebied)
            locaties.append(locatie)

        gio: PublicationGio = PublicationGio(
            source_codes=input_aanwijzing.gebied_codes,
            title=input_aanwijzing.title,
            frbr=self._build_frbr_aanwijzing(input_aanwijzing),
            new=True,
            geboorteregeling=self._act_frbr.get_work(),
            achtergrond_verwijzing="TOP10NL",
            achtergrond_actualiteit=str(input_aanwijzing.modified_date)[:10],
            locaties=locaties,
        )

        # Save to accumulator
        self._result.gios[gio.key()] = gio
        return gio

    def _area_to_locatie(self, area: AreasTable, input_gebied: InputGebied) -> PublicationGioLocatie:
        gml_hash = hashlib.sha512()
        gml_hash.update(area.Gml.encode())

        return PublicationGioLocatie(
            code=input_gebied.code,
            title=input_gebied.title,
            basisgeo_id=str(input_gebied.basisgeo_id),
            # str(hash) is what we did before, so thats how the hashes are stored in the state
            source_hash=str(gml_hash),
            gml=area.Gml,
        )

    def _build_frbr_aanwijzing(self, input_aanwijzing: GebiedsaanwijzingData) -> dso_models.GioFRBR:
        # Note: Gebieden are consolidated per Act, so we use the Act's Work_Date
        # and make their identifier unique with act data.
        # The identifier should be unique for this Geo/gio which is a bummer because we have not stored this in our database
        # but we can get away with it by using al Object_ID's of the used gebieden
        source_object_ids: List[int] = sorted(
            [
                int(code.split("-")[1])  # Gets the Object_ID part from the code
                for code in input_aanwijzing.gebied_codes
            ]
        )
        # We needed to cast it to ints first to get the correct sorting
        # But now we need to make it strings again for concatenating
        source_object_str_ids: List[str] = [str(x) for x in source_object_ids]
        unique_code: str = f"GA-{'-'.join(source_object_str_ids)}"

        work_date: str = self._act_frbr.Work_Date
        work_identifier = f"{self._act_frbr.Act_ID}-{self._act_frbr.Expression_Version}-{unique_code}"
        return dso_models.GioFRBR(
            Work_Province_ID=self._act_frbr.Work_Province_ID,
            Work_Date=work_date,
            Work_Other=work_identifier,
            Expression_Language=self._act_frbr.Expression_Language,
            Expression_Date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            Expression_Version=1,
        )

    def _fetch_area(self, area_uuid: UUID) -> AreasTable:
        area: Optional[AreasTable] = self._area_repository.get_with_gml(self._session, area_uuid)
        if area is None:
            raise RuntimeError(f"Area UUID {area_uuid} does not exist")
        return area


class PublicationGiosProviderFactory:
    def __init__(self, area_repository: AreaRepository):
        self._area_repository: AreaRepository = area_repository

    def process(
        self,
        session: Session,
        act_frbr: ActFrbr,
        gebieden_data: GebiedenData,
        gebiedsaanwijzingen: List[GebiedsaanwijzingData],
    ) -> PublicationGeoData:
        service: PublicationGiosProvider = PublicationGiosProvider(
            session,
            self._area_repository,
            act_frbr,
        )
        return service.resolve_geo(gebieden_data, gebiedsaanwijzingen)
