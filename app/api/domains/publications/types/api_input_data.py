from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional

from app.api.domains.publications.types.enums import MutationStrategy, PackageType, PurposeType
from app.api.domains.publications.types.models import AnnouncementContent, AnnouncementMetadata, AnnouncementProcedural
from app.core.tables.publications import PublicationAnnouncementTable, PublicationVersionTable
from typing import Set

from pydantic import BaseModel, Field
import dso.models as dso_models


@dataclass
class BillFrbr:
    Work_Province_ID: str
    Work_Country: str
    Work_Date: str
    Work_Other: str

    Expression_Language: str
    Expression_Date: str
    Expression_Version: int

    def get_work(self) -> str:
        work: str = f"/akn/{self.Work_Country}/bill/{self.Work_Province_ID}/{self.Work_Date}/{self.Work_Other}"
        return work

    def get_expression_version(self) -> str:
        expression: str = f"{self.Expression_Language}@{self.Expression_Date};{self.Expression_Version}"
        return expression


@dataclass
class ActFrbr:
    Act_ID: int

    Work_Province_ID: str
    Work_Country: str
    Work_Date: str
    Work_Other: str

    Expression_Language: str
    Expression_Date: str
    Expression_Version: int

    def get_work(self) -> str:
        work: str = f"/akn/{self.Work_Country}/act/{self.Work_Province_ID}/{self.Work_Date}/{self.Work_Other}"
        return work

    def get_expression_version(self) -> str:
        expression: str = f"{self.Expression_Language}@{self.Expression_Date};{self.Expression_Version}"
        return expression

    def __repr__(self) -> str:
        return f"""
        ActFrbr(
            Work={self.get_work()},
            Expression_Version={self.get_expression_version()},
        )
        """


@dataclass
class DocFrbr:
    Document_Type: str

    Work_Province_ID: str
    Work_Country: str
    Work_Date: str
    Work_Other: str

    Expression_Language: str
    Expression_Date: str
    Expression_Version: int

    def get_work(self) -> str:
        work: str = f"/akn/{self.Work_Country}/doc/{self.Work_Province_ID}/{self.Work_Date}/{self.Work_Other}"
        return work

    def get_expression_version(self) -> str:
        expression: str = f"{self.Expression_Language}@{self.Expression_Date};{self.Expression_Version}"
        return expression


@dataclass
class Purpose:
    Purpose_Type: PurposeType
    Effective_Date: Optional[date]
    Work_Province_ID: str
    Work_Date: str
    Work_Other: str


class PublicationGioLocatie(BaseModel):
    code: str  # code of 'gebied' like 'gebied-1'
    title: str
    # Also used in OW as the link from OW to GIO
    # I think its save to use the area_uuid as its unique for the geometry
    # And if we find a match when loading from state, then we will overwrite this
    basisgeo_id: str
    # Used to conclude if we have new version
    source_hash: str

    # Gml in the GIO
    gml: str

    def key(self) -> str:
        return self.code


class PublicationGio(BaseModel):
    source_codes: Set[str]
    title: str

    frbr: dso_models.FRBR
    new: bool

    geboorteregeling: str
    achtergrond_verwijzing: str
    achtergrond_actualiteit: str

    locaties: List[PublicationGioLocatie]

    # We are using the set source_codes as our reference key
    # But we convert it to a string for convenience, mainly because our DSO OW system
    # uses source_code as a string
    def key(self) -> str:
        return "_".join(sorted(self.source_codes))


class PublicationGebiedengroep(BaseModel):
    uuid: str
    code: str
    title: str
    source_gebieden_codes: Set[str]
    gio_keys: Set[str]

    def key(self) -> str:
        return "_".join(sorted(self.gio_keys))


class PublicationGebiedsaanwijzing(BaseModel):
    uuid: str  # Used as a lookup key in DSO
    aanwijzing_type: str
    aanwijzing_group: str
    title: str  # Used everywhere except the inline html <a>{inline_title}</a>
    # Used to determine reuse and target to geo_gio
    source_target_codes: Set[str]
    source_gebied_codes: Set[str]
    gio_key: str

    def key(self) -> str:
        code_parts: str = "_".join(sorted(self.source_gebied_codes))
        return "-".join(
            [
                code_parts,
                self.aanwijzing_type,
                self.aanwijzing_group,
            ]
        )


class PublicationGeoData(BaseModel):
    gios: Dict[str, PublicationGio] = Field(default_factory=dict)
    gebiedengroepen: Dict[str, PublicationGebiedengroep] = Field(default_factory=dict)
    gebiedsaanwijzingen: Dict[str, PublicationGebiedsaanwijzing] = Field(default_factory=dict)


@dataclass
class PublicationData:
    used_object_codes: Set[str]
    objects: List[dict]
    documents: List[dict]
    assets: List[dict]
    gios: Dict[str, PublicationGio]
    gebiedengroepen: Dict[str, PublicationGebiedengroep]
    gebiedsaanwijzingen: Dict[str, PublicationGebiedsaanwijzing]
    bill_attachments: List[Dict]
    area_of_jurisdiction: dict
    parsed_template: str


@dataclass
class ActMutation:
    Consolidated_Act_Frbr: ActFrbr
    Consolidated_Act_Text: str
    Known_Wid_Map: Dict[str, str]
    Known_Wids: List[str]
    Removed_Gios: List[dict]


@dataclass
class ApiActInputData:
    Bill_Frbr: BillFrbr
    Act_Frbr: ActFrbr
    Consolidation_Purpose: Purpose
    Publication_Data: PublicationData
    Package_Type: PackageType
    Publication_Version: PublicationVersionTable
    Act_Mutation: Optional[ActMutation]
    Ow_State: Optional[str]
    Mutation_Strategy: MutationStrategy


@dataclass
class ApiAnnouncementInputData:
    Doc_Frbr: DocFrbr
    About_Bill_Frbr: BillFrbr
    About_Act_Frbr: ActFrbr
    Package_Type: PackageType
    Announcement: PublicationAnnouncementTable
    Announcement_Metadata: AnnouncementMetadata
    Announcement_Procedural: AnnouncementProcedural
    Announcement_Content: AnnouncementContent
