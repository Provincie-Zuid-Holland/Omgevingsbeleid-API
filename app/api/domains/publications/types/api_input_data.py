from dataclasses import dataclass
from datetime import date

import dso.models as dso_models
from pydantic import BaseModel, Field

from app.api.domains.publications.types.enums import MutationStrategy, PackageType, PurposeType
from app.api.domains.publications.types.models import AnnouncementContent, AnnouncementMetadata, AnnouncementProcedural
from app.core.tables.publications import PublicationAnnouncementTable, PublicationVersionTable


@dataclass
class BillFrbr:
    work_province_id: str
    work_country: str
    work_date: str
    work_other: str

    expression_language: str
    expression_date: str
    expression_version: int

    def get_work(self) -> str:
        work: str = f"/akn/{self.work_country}/bill/{self.work_province_id}/{self.work_date}/{self.work_other}"
        return work

    def get_expression_version(self) -> str:
        expression: str = f"{self.expression_language}@{self.expression_date};{self.expression_version}"
        return expression


@dataclass
class ActFrbr:
    act_id: int

    work_province_id: str
    work_country: str
    work_date: str
    work_other: str

    expression_language: str
    expression_date: str
    expression_version: int

    def get_work(self) -> str:
        work: str = f"/akn/{self.work_country}/act/{self.work_province_id}/{self.work_date}/{self.work_other}"
        return work

    def get_expression_version(self) -> str:
        expression: str = f"{self.expression_language}@{self.expression_date};{self.expression_version}"
        return expression

    def __repr__(self) -> str:
        return f"""
        ActFrbr(
            Work={self.get_work()},
            expression_version={self.get_expression_version()},
        )
        """


@dataclass
class DocFrbr:
    document_type: str

    work_province_id: str
    work_country: str
    work_date: str
    work_other: str

    expression_language: str
    expression_date: str
    expression_version: int

    def get_work(self) -> str:
        work: str = f"/akn/{self.work_country}/doc/{self.work_province_id}/{self.work_date}/{self.work_other}"
        return work

    def get_expression_version(self) -> str:
        expression: str = f"{self.expression_language}@{self.expression_date};{self.expression_version}"
        return expression


@dataclass
class Purpose:
    purpose_type: PurposeType
    effective_date: date | None
    work_province_id: str
    work_date: str
    work_other: str


class PublicationGioLocatie(BaseModel):
    code: str  # code of 'gebied' like 'gebied-1'
    title: str
    # Also used in OW as the link from OW to GIO
    # I think its save to use the area_id as its unique for the geometry
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
    id: str
    code: str
    title: str
    source_gebieden_codes: set[str]
    gio_key: str


class PublicationGebiedsaanwijzing(BaseModel):
    id: str
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
    consolidated_act_frbr: ActFrbr
    consolidated_act_text: str
    known_wid_map: dict[str, str]
    known_wids: list[str]
    removed_gios: list[dict]


@dataclass
class ApiActInputData:
    bill_frbr: BillFrbr
    act_frbr: ActFrbr
    consolidation_purpose: Purpose
    publication_data: PublicationData
    package_type: PackageType
    publication_version: PublicationVersionTable
    act_mutation: ActMutation | None
    ow_state: str | None
    mutation_strategy: MutationStrategy


@dataclass
class ApiAnnouncementInputData:
    doc_frbr: DocFrbr
    about_bill_frbr: BillFrbr
    about_act_frbr: ActFrbr
    package_type: PackageType
    announcement: PublicationAnnouncementTable
    announcement_metadata: AnnouncementMetadata
    announcement_procedural: AnnouncementProcedural
    announcement_content: AnnouncementContent
