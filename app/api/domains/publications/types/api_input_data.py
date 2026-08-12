from dataclasses import dataclass
from datetime import date

import dso.models as dso_models
from pydantic import BaseModel, Field

from app.api.domains.publications.types.enums import MutationStrategy, PackageType, PurposeType
from app.api.domains.publications.types.models import AnnouncementContent, AnnouncementMetadata, AnnouncementProcedural
from app.core.tables.publications import PublicationAnnouncementTable, PublicationVersionTable


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
    Effective_Date: date | None
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
    key: str
    source_codes: set[str]
    title: str

    frbr: dso_models.FRBR
    new: bool

    geboorteregeling: str
    achtergrond_verwijzing: str
    achtergrond_actualiteit: str

    locaties: list[PublicationGioLocatie]

    def has_same_data(self, other: "PublicationGio") -> bool:
        if self.title != other.title:
            return False

        self_locs = sorted((loc.title, loc.source_hash) for loc in self.locaties)
        other_locs = sorted((loc.title, loc.source_hash) for loc in other.locaties)
        return self_locs == other_locs


class PublicationGebiedengroep(BaseModel):
    uuid: str
    code: str
    title: str
    source_gebieden_codes: set[str]
    gio_key: str


class PublicationGebiedsaanwijzing(BaseModel):
    uuid: str
    code: str
    title: str  # Used everywhere except the inline html <a>{inline_title}</a>
    aanwijzing_type: str
    aanwijzing_group: str
    gio_key: str

    # Used to determine reuse and target to geo_gio
    # @note: unused at the moment, but useful to have in the state machine
    #           Else we can not conclude reuse in the next version
    source_target_codes: set[str]
    resolved_gebied_codes: set[str]


class PublicationGeoData(BaseModel):
    gios: dict[str, PublicationGio] = Field(default_factory=dict)
    gebiedengroepen: dict[str, PublicationGebiedengroep] = Field(default_factory=dict)
    gebiedsaanwijzingen: dict[str, PublicationGebiedsaanwijzing] = Field(default_factory=dict)


@dataclass
class PublicationData:
    all_object_codes: set[str]
    all_objects: list[dict]
    used_object_codes: set[str]
    used_objects: list[dict]
    documents: list[dict]
    assets: list[dict]
    gios: dict[str, PublicationGio]
    gebiedengroepen: dict[str, PublicationGebiedengroep]
    gebiedsaanwijzingen: dict[str, PublicationGebiedsaanwijzing]
    bill_attachments: list[dict]
    area_of_jurisdiction: dict
    parsed_template: str


@dataclass
class ActMutation:
    Consolidated_Act_Frbr: ActFrbr
    Consolidated_Act_Text: str
    Known_Wid_Map: dict[str, str]
    Known_Wids: list[str]
    Removed_Gios: list[dict]


@dataclass
class ApiActInputData:
    Bill_Frbr: BillFrbr
    Act_Frbr: ActFrbr
    Consolidation_Purpose: Purpose
    Publication_Data: PublicationData
    Package_Type: PackageType
    Publication_Version: PublicationVersionTable
    Act_Mutation: ActMutation | None
    Ow_State: str | None
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
