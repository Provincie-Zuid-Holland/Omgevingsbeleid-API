import hashlib
from re import M, X
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field

from app.api.domains.publications.services.act_package.publication_gebieden_provider import GebiedenData, InputGebied, InputGebiedengroep
from app.api.domains.publications.services.act_package.publication_gebiedsaanwijzing_provider import (
    GebiedsaanwijzingData,
)
import dso.models as dso_models
from sqlalchemy.orm import Session

from app.api.domains.publications.types.api_input_data import ActFrbr
from app.api.domains.werkingsgebieden.repositories.area_repository import AreaRepository
from app.core.tables.others import AreasTable


class InputGeoGio(BaseModel):
    uuid: UUID
    code: str
    area_uuid: UUID
    # We overwrite this with the area.Title at the moment
    # But I think we should use the objects title instead as we can modify it
    # @todo: need to do research if we can change the title of a GIO
    title: str
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


class PublicationGeoLocatie(BaseModel):
    title: str
    # Also used in OW as the link from OW to GIO
    # I think its save to use the area_uuid as its unique for the geometry
    # And if we find a match when loading from state, then we will overwrite this
    basisgeo_id: str 
    # Used to conclude if we have new version
    source_hash: str
    source_code: str
    
    def key(self) -> str:
        return self.source_code


class PublicationGeoGio(BaseModel):
    geboorteregeling: str
    achtergrond_verwijzing: str
    achtergrond_actualiteit: str
    frbr: dso_models.FRBR
    title: str
    locaties: List[PublicationGeoLocatie]
    source_codes: Set[str]

    # We are using the set source_codes as our reference key
    # But we convert it to a string for convenience, mainly because our DSO OW system
    # uses source_code as a string
    def key(self) -> str:
        return ",".join(sorted(self.source_codes))


class PublicationGebied(BaseModel):
    uuid: str
    object_id: int
    code: str
    title: str
    geo_gio_key: str

    def key(self) -> str:
        return self.code


class PublicationGebiedengroep(BaseModel):
    uuid: str
    object_id: int
    code: str
    title: str
    gebied_codes: Set[str]

    def key(self) -> str:
        return ",".join(sorted(self.gebied_codes))


class PublicationGebiedsaanwijzing(BaseModel):
    # Its `text_uuid` instead of `uuid` because its just a temp uuid to glue it in the dso.RegelingTekst
    text_uuid: str
    aanwijzing_type: str
    aanwijzing_group: str
    title: str
    # Used to determine reuse and target to geo_gio
    source_target_codes: Set[str]
    source_gebied_codes: Set[str]
    geo_gio_key: str

    def key(self) -> str:
        return ",".join(sorted(self.source_gebied_codes))


class PublicationGeoData(BaseModel):
    geo_gios: Dict[str, PublicationGeoGio] = Field(default_factory=dict)
    gebieden: Dict[str, PublicationGebied] = Field(default_factory=dict)
    gebiedengroepen: Dict[str, PublicationGebiedengroep] = Field(default_factory=dict)
    gebiedsaanwijzingen: Dict[str, PublicationGebiedsaanwijzing] = Field(default_factory=dict)


class PublicationGeoGiosProvider:
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
        self._resolve_gebieden(gebieden_data.used_gebieden)
        self._resolve_gebiedengroepen(gebieden_data.used_gebiedengroepen)
        self._resolve_gebiedsaanwijzingen(gebieden_data, gebiedsaanwijzingen)

        return self._result

    def _resolve_gebieden(self, used_gebieden: List[InputGebied]):
        for input_gebied in used_gebieden:
            area: AreasTable = self._fetch_area(input_gebied.area_uuid)
            gio: PublicationGeoGio = self._inputgebied_to_gio(input_gebied, area)
            gebied: PublicationGebied = PublicationGebied(
                uuid=str(input_gebied.uuid),
                object_id=input_gebied.object_id,
                code=input_gebied.code,
                title=input_gebied.title,
                geo_gio_key=gio.key(),
            )
            # Save to accumulator
            self._result.gebieden[gebied.code] = gebied

    def _resolve_gebiedengroepen(self, used_gebiedengroepen: List[InputGebiedengroep]):
        for input_groep in used_gebiedengroepen:
            groep: PublicationGebiedengroep = PublicationGebiedengroep(
                uuid=str(input_groep.uuid),
                object_id=input_groep.object_id,
                code=input_groep.code,
                title=input_groep.title,
                gebied_codes=input_groep.gebied_codes,
            )
            # Save to accumulator
            self._result.gebiedengroepen[groep.key()] = groep

    def _resolve_gebiedsaanwijzingen(
        self,
        gebieden_data: GebiedenData,
        gebiedsaanwijzingen: List[GebiedsaanwijzingData],
    ):
        for input_aanwijzing in gebiedsaanwijzingen:
            gio: PublicationGeoGio = self._resolve_gio_for_aanwijzing(gebieden_data, input_aanwijzing)
            aanwijzing: PublicationGebiedsaanwijzing = PublicationGebiedsaanwijzing(
                text_uuid=input_aanwijzing.text_uuid,
                aanwijzing_type=input_aanwijzing.aanwijzing_type,
                aanwijzing_group=input_aanwijzing.aanwijzing_group,
                title=input_aanwijzing.title,
                source_target_codes=input_aanwijzing.source_target_codes,
                source_gebied_codes=input_aanwijzing.gebied_codes,
                geo_gio_key=gio.key(),
            )
            # Save to accumulator
            self._result.gebiedsaanwijzingen[aanwijzing.key()] = aanwijzing

    def _fetch_area(self, area_uuid: UUID) -> AreasTable:
        area: Optional[AreasTable] = self._area_repository.get_with_gml(self._session, area_uuid)
        if area is None:
            raise RuntimeError(f"Area UUID {area_uuid} does not exist")
        return area

    def _inputgebied_to_gio(self, input_gebied: InputGebied, area: AreasTable) -> PublicationGeoGio:
        gml_hash = hashlib.sha512()
        gml_hash.update(area.Gml.encode())
    
        gio: PublicationGeoGio = PublicationGeoGio(
            geboorteregeling=self._act_frbr.get_work(),
            achtergrond_verwijzing="TOP10NL",
            achtergrond_actualiteit=str(input_gebied.modified_date)[:10],
            frbr=self._build_frbr_gebied(input_gebied),
            title=area.Source_Title,
            locaties=[
                PublicationGeoLocatie(
                    title=area.Source_Title,
                    basisgeo_id=str(area.UUID),
                    source_hash=str(gml_hash), # str(hash) is what we did before, so thats how the hashes are stored in the state
                    source_code=input_gebied.code,
                )
            ],
            source_codes=set([input_gebied.code]),
        )
        
        # Save to accumulator
        self._result.geo_gios[gio.key()] = gio
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

    def _resolve_gio_for_aanwijzing(self, gebieden_data: GebiedenData, input_aanwijzing: GebiedsaanwijzingData) -> PublicationGeoGio:
        # It could be that we have this GeoGio already because the `Gebied` made it
        # or another `Gebiedsaanwijzing` made it
        gio_key: str = ",".join(sorted(input_aanwijzing.gebied_codes))
        existing_gio: Optional[PublicationGeoGio] = self._result.geo_gios.get(gio_key)
        if existing_gio is not None:
            return existing_gio
        
        # Make the GIO based on all gebied codes in the input_aanwijzing.
        # Note that these might not exists in the "used_" selection.
        # So we need to dig into GebiedenData.all_gebieden
        locaties: List[PublicationGeoLocatie] = []
        for gebied_code in input_aanwijzing.gebied_codes:
            input_gebied: Optional[InputGebied] = gebieden_data.all_gebieden.get(gebied_code)
            if input_gebied is None:
                raise RuntimeError(f"Gebiedsaanwijzijng `{input_aanwijzing.title}` points to unknown gebied `{gebied_code}`")
            area: AreasTable = self._fetch_area(input_gebied.area_uuid)
            locatie: PublicationGeoLocatie = self._area_to_locatie(area,  gebied_code)
            locaties.append(locatie)
        
        gio: PublicationGeoGio = PublicationGeoGio(
            geboorteregeling=self._act_frbr.get_work(),
            achtergrond_verwijzing="TOP10NL",
            achtergrond_actualiteit=str(input_aanwijzing.modified_date)[:10],
            frbr=self._build_frbr_aanwijzing(input_aanwijzing),
            title=input_aanwijzing.title,
            locaties=locaties,
            source_codes=input_aanwijzing.gebied_codes,
        )
        
        # Save to accumulator
        self._result.geo_gios[gio.key()] = gio
        return gio

    def _area_to_locatie(self, area: AreasTable, gebied_code: str) -> PublicationGeoLocatie:
        gml_hash = hashlib.sha512()
        gml_hash.update(area.Gml.encode())
        
        return PublicationGeoLocatie(
            title=area.Source_Title,
            basisgeo_id=str(area.UUID),
            source_hash=str(gml_hash), # str(hash) is what we did before, so thats how the hashes are stored in the state
            source_code=gebied_code,
        )

    def _build_frbr_aanwijzing(self, input_aanwijzing: GebiedsaanwijzingData) -> dso_models.GioFRBR:
        # Note: Gebieden are consolidated per Act, so we use the Act's Work_Date
        # and make their identifier unique with act data.
        # The identifier should be unique for this Geo/gio which is a bummer because we have not stored this in our database
        # but we can get away with it by using al Object_ID's of the used gebieden
        source_object_ids: List[int] = sorted([
            int(code.split("-")[1]) # Gets the Object_ID part from the code
            for code in input_aanwijzing.gebied_codes
        ])
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


class PublicationGeoGiosProviderFactory:
    def __init__(self, area_repository: AreaRepository):
        self._area_repository: AreaRepository = area_repository
    
    def process(
        self,
        session: Session,
        act_frbr: ActFrbr,
        gebieden_data: GebiedenData,
        gebiedsaanwijzingen: List[GebiedsaanwijzingData],
    ) -> PublicationGeoData:
        service: PublicationGeoGiosProvider = PublicationGeoGiosProvider(
            session,
            self._area_repository,
            act_frbr,
        )
        return service.resolve_geo(gebieden_data, gebiedsaanwijzingen)
