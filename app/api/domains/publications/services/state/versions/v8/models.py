from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

CustomSetStr = Annotated[set[str], PlainSerializer(lambda x: list(x), return_type=list[str])]


class Purpose(BaseModel):
    purpose_type: str
    effective_date: str | None = None
    work_province_id: str
    work_date: str
    work_other: str

    def get_frbr_work(self) -> str:
        result: str = f"/join/id/proces/{self.work_province_id}/{self.work_date}/{self.work_other}"
        return result


class Frbr(BaseModel):
    work_province_id: str
    work_country: str
    work_date: str
    work_other: str
    expression_language: str
    expression_date: str
    expression_version: int


class GioLocatie(BaseModel):
    title: str
    basisgeo_id: str  # Also used in OW as the link from OW to GIO
    source_hash: str  # Hash of the GML/Geometry so we wont need to store the GML
    source_code: str  # This always is a gebied code like `gebied-1`


class Gio(BaseModel):
    # The GIO key will be the `code` from the source, as that is unique enough for now
    # Since the latest communications it's oke if we generate 1 GIO per gebiedengroep/gebiedsaanwijzing.
    # Even if they have the same locations
    #
    # We do keep this Gio model separate as there has been lots of discussions about it with DSO
    # And keeping it separated (as I already build it this way) allows us to build a borrowing/reuse system later if needed
    key: str

    # This is to determine what and who's this is
    # For a simple Gebied this will be ["gebied-1"]
    # But for a composite GIO like for a gebiedsaanwijzing, this could be ["gebied-1", "gebied-2", "gebied-3"]
    # Even though the gebiedsaanwijzing might actually point to a Gebiedengroep.
    # But a gebiedengroep is unreliable as the code of a gebiedengroep does not tell us if gebieden got added or removed.
    source_codes: CustomSetStr = Field(default_factory=set)

    # Used on top of the GeoInformatieObjectVaststelling and Aanlevering
    # If there is only 1 `locatie` then it's probably the same title as the locatie.title
    # If there is more than 1 locatie, then it's probably the name of the Gebiedengroep Or Gebiedsaanwijzing
    title: str

    frbr: Frbr

    geboorteregeling: str
    achtergrond_verwijzing: str
    achtergrond_actualiteit: str

    # These are the <geo:locaties> in <geo:GeoInformatieObjectVaststelling>
    # These are represent gebied in ow
    locaties: list[GioLocatie] = Field(default_factory=list)


class Gebiedengroep(BaseModel):
    id: str
    code: str
    title: str
    source_gebieden_codes: CustomSetStr
    gio_key: str  # Points to a Gio in the same state. Not stable across publications


class Gebiedsaanwijzing(BaseModel):
    code: str
    aanwijzing_type: str
    aanwijzing_group: str
    title: str
    # Used to determine reuse and target to geo_gio
    source_target_codes: CustomSetStr
    resolved_gebied_codes: CustomSetStr
    gio_key: str  # Points to a Gio in the same state. Not stable across publications


class Document(BaseModel):
    id: str
    code: str
    frbr: Frbr
    filename: str
    title: str
    owner_act: str
    content_type: str
    object_id: int
    hash: str


class Asset(BaseModel):
    id: str


class WidData(BaseModel):
    known_wid_map: dict[str, str]
    known_wids: list[str]


# OwState
class AbstractRef(BaseModel):
    pass


class AbstractLocationRef(AbstractRef):
    ref_type: str = Field(..., description="Type discriminator")


class UnresolvedAmbtsgebiedRef(AbstractLocationRef):
    ref_type: Literal["unresolved_ambtsgebied"] = "unresolved_ambtsgebied"


class AmbtsgebiedRef(AbstractLocationRef):
    ref_type: Literal["ambtsgebied"] = "ambtsgebied"
    ref: str


class UnresolvedGebiedRef(AbstractLocationRef):
    ref_type: Literal["unresolved_gebied"] = "unresolved_gebied"
    target_code: str


class GebiedRef(UnresolvedGebiedRef):
    ref_type: Literal["gebied"] = "gebied"
    ref: str


class UnresolvedGebiedengroepRef(AbstractLocationRef):
    ref_type: Literal["unresolved_gebiedengroep"] = "unresolved_gebiedengroep"
    target_code: str


class GebiedengroepRef(UnresolvedGebiedengroepRef):
    ref_type: Literal["gebiedengroep"] = "gebiedengroep"
    ref: str


LocationRefUnion = Annotated[
    AmbtsgebiedRef
    | UnresolvedAmbtsgebiedRef
    | GebiedRef
    | UnresolvedGebiedRef
    | GebiedengroepRef
    | UnresolvedGebiedengroepRef,
    Field(discriminator="ref_type"),
]


# Gebiedsaanwijzing Ref
class AbstractGebiedsaanwijzingRef(AbstractRef):
    ref_type: str = Field(..., description="Type discriminator")


class UnresolvedGebiedsaanwijzingRef(AbstractGebiedsaanwijzingRef):
    ref_type: Literal["unresolved_gebiedsaanwijzing"] = "unresolved_gebiedsaanwijzing"
    target_key: str


class GebiedsaanwijzingRef(UnresolvedGebiedsaanwijzingRef):
    ref_type: Literal["gebiedsaanwijzing"] = "gebiedsaanwijzing"
    ref: str


GebiedsaanwijzingRefUnion = Annotated[
    UnresolvedGebiedsaanwijzingRef | GebiedsaanwijzingRef,
    Field(discriminator="ref_type"),
]


class AbstractWidRef(AbstractRef):
    ref_type: str = Field(..., description="Type discriminator")


class UnresolvedDivisieRef(AbstractWidRef):
    ref_type: Literal["unresolved_divisie"] = "unresolved_divisie"
    target_wid: str


class DivisieRef(UnresolvedDivisieRef):
    ref_type: Literal["divisie"] = "divisie"
    ref: str


class UnresolvedDivisietekstRef(AbstractWidRef):
    ref_type: Literal["unresolved_divisietekst"] = "unresolved_divisietekst"
    target_wid: str


class DivisietekstRef(UnresolvedDivisietekstRef):
    ref_type: Literal["divisietekst"] = "divisietekst"
    ref: str


WidRefUnion = Annotated[
    DivisieRef | UnresolvedDivisieRef | DivisietekstRef | UnresolvedDivisietekstRef,
    Field(discriminator="ref_type"),
]


class OwObjectStatus(str, Enum):
    new = "new"
    changed = "changed"
    unchanged = "unchanged"
    deleted = "deleted"


class StrictBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class BaseOwObject(StrictBase):
    identification: str
    object_status: OwObjectStatus = Field(OwObjectStatus.unchanged)
    procedure_status: str | None = Field(None)


class OwAmbtsgebied(BaseOwObject):
    source_uuid: str
    administrative_borders_id: str
    domain: str
    valid_on: str
    title: str

    def __hash__(self):
        return hash(("ambtsgebied",))


class OwRegelingsgebied(BaseOwObject):
    source_uuid: str
    locatie_ref: LocationRefUnion

    def __hash__(self):
        return hash(("regelingsgebied",))


class OwGebied(BaseOwObject):
    source_code: str
    title: str
    geometry_ref: str

    def __hash__(self):
        return hash((self.source_code,))


class OwGebiedengroep(BaseOwObject):
    source_code: str
    title: str
    gebieden_refs: list[LocationRefUnion] = Field(default_factory=list)

    def __hash__(self):
        return hash((self.source_code,))


class OwDivisie(BaseOwObject):
    source_uuid: str
    source_code: str
    wid: str

    def __hash__(self):
        return hash((self.wid,))


class OwDivisietekst(BaseOwObject):
    source_uuid: str
    source_code: str
    wid: str

    def __hash__(self):
        return hash((self.wid,))


class OwGebiedsaanwijzing(BaseOwObject):
    source_code: str
    title: str
    indication_type: str
    indication_group: str
    location_refs: list[LocationRefUnion] = Field(default_factory=list)

    def __hash__(self):
        return hash((self.source_code,))


class OwTekstdeel(BaseOwObject):
    source_uuid: str
    source_code: str
    idealization: str
    text_ref: WidRefUnion
    location_refs: list[LocationRefUnion] = Field(default_factory=list)
    gebiedsaanwijzing_refs: list[GebiedsaanwijzingRefUnion] = Field(default_factory=list)
    themas: list[str] = Field(default_factory=list)

    def __hash__(self):
        return hash((self.source_code,))


class OwState(StrictBase):
    ambtsgebieden: list[OwAmbtsgebied] = Field(default_factory=list)
    regelingsgebieden: list[OwRegelingsgebied] = Field(default_factory=list)
    gebieden: list[OwGebied] = Field(default_factory=list)
    gebiedengroepen: list[OwGebiedengroep] = Field(default_factory=list)
    gebiedsaanwijzingen: list[OwGebiedsaanwijzing] = Field(default_factory=list)
    divisies: list[OwDivisie] = Field(default_factory=list)
    divisieteksten: list[OwDivisietekst] = Field(default_factory=list)
    tekstdelen: list[OwTekstdeel] = Field(default_factory=list)


# Acts
class ActiveAct(BaseModel):
    act_frbr: Frbr
    bill_frbr: Frbr
    consolidation_purpose: Purpose
    document_type: str
    procedure_type: str
    gios: dict[str, Gio] = Field(default_factory=dict)
    gebiedengroepen: dict[str, Gebiedengroep] = Field(default_factory=dict)
    gebiedsaanwijzingen: dict[str, Gebiedsaanwijzing] = Field(default_factory=dict)
    documents: dict[int, Document] = Field(default_factory=dict)
    assets: dict[str, Asset] = Field(default_factory=dict)
    wid_data: WidData
    ow_state: OwState
    act_text: str
    publication_version_id: str
    model_config = ConfigDict(from_attributes=True)


class ActiveAnnouncement(BaseModel):
    doc_frbr: Frbr
    about_act_frbr: Frbr
    about_bill_frbr: Frbr
    document_type: str
    procedure_type: str
