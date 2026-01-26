from typing import Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict, Field

from enum import Enum
from typing import Annotated, Literal, Union


class Purpose(BaseModel):
    Purpose_Type: str
    Effective_Date: Optional[str] = None
    Work_Province_ID: str
    Work_Date: str
    Work_Other: str

    def get_frbr_work(self) -> str:
        result: str = f"/join/id/proces/{self.Work_Province_ID}/{self.Work_Date}/{self.Work_Other}"
        return result


class Frbr(BaseModel):
    Work_Province_ID: str
    Work_Country: str
    Work_Date: str
    Work_Other: str
    Expression_Language: str
    Expression_Date: str
    Expression_Version: int


class GioLocatie(BaseModel):
    title: str
    basisgeo_id: str  # Also used in OW as the link from OW to GIO
    source_hash: str  # Hash of the GML/Geometry so we wont need to store the GML
    source_code: str  # This always is a gebied code like `gebied-1`


class Gio(BaseModel):
    """
    Gio was managed by the Werkingsgebied before this transition.
    """

    # This is to determine what and whos this is
    # For a simple Gebied this will be ["gebied-1"]
    # But for a composite GIO like for an gebiedsaanwijzing, this could be ["gebied-1", "gebied-2", "gebied-3"]
    # Eventhough the gebiedsaanwijzing might actually point to a Gebiedengroep.
    # But a gebiedengroep is unreliable as the code of a gebiedengroep does not tell us if gebieden got added or removed.
    source_codes: Set[str] = Field(default_factory=set)

    # Used on top of the GeoInformatieObjectVaststelling and Aanlevering
    # If there is only 1 `locatie` then its probably the same title as the locatie.title
    # If there is more then 1 locatie, then its probably the name of the Gebiedengroep Or Gebiedsaanwijzing
    title: str

    frbr: Frbr

    geboorteregeling: str
    achtergrond_verwijzing: str
    achtergrond_actualiteit: str

    # These are the <geo:locaties> in <geo:GeoInformatieObjectVaststelling>
    # These are represent gebied in ow
    locaties: List[GioLocatie] = Field(default_factory=list)

    # We are using the set source_codes as our reference key
    # But we convert it to a string for convenience, mainly because our DSO OW system
    # uses source_code as a string
    def key(self) -> str:
        return "_".join(sorted(self.source_codes))

    def get_code(self) -> str:
        return self.key()


class Gebiedengroep(BaseModel):
    uuid: str
    code: str
    title: str
    source_gebieden_codes: Set[str]
    gio_keys: Set[str]


class Gebiedsaanwijzing(BaseModel):
    uuid: str
    aanwijzing_type: str
    aanwijzing_group: str
    title: str
    # Used to determine reuse and target to geo_gio
    source_target_codes: Set[str]
    source_gebied_codes: Set[str]
    gio_key: str


class Document(BaseModel):
    UUID: str
    Code: str
    Frbr: Frbr
    Filename: str
    Title: str
    Owner_Act: str
    Content_Type: str
    Object_ID: int
    Hash: str


class Asset(BaseModel):
    UUID: str


class WidData(BaseModel):
    Known_Wid_Map: Dict[str, str]
    Known_Wids: List[str]


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
    Union[
        AmbtsgebiedRef,
        UnresolvedAmbtsgebiedRef,
        GebiedRef,
        UnresolvedGebiedRef,
        GebiedengroepRef,
        UnresolvedGebiedengroepRef,
    ],
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
    Union[
        UnresolvedGebiedsaanwijzingRef,
        GebiedsaanwijzingRef,
    ],
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
    Union[
        DivisieRef,
        UnresolvedDivisieRef,
        DivisietekstRef,
        UnresolvedDivisietekstRef,
    ],
    Field(discriminator="ref_type"),
]


class OwObjectStatus(str, Enum):
    new = "new"
    changed = "changed"
    unchanged = "unchanged"
    deleted = "deleted"


class BaseOwObject(BaseModel):
    identification: str
    object_status: OwObjectStatus = Field(OwObjectStatus.unchanged)
    procedure_status: Optional[str] = Field(None)
    model_config = ConfigDict(from_attributes=True)


class OwAmbtsgebied(BaseOwObject):
    source_uuid: str
    administrative_borders_id: str
    domain: str
    valid_on: str
    title: str
    model_config = ConfigDict(from_attributes=True)

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
    gebieden_refs: List[LocationRefUnion] = Field(default_factory=list)

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
    location_refs: List[LocationRefUnion] = Field(default_factory=list)

    def __hash__(self):
        return hash((self.source_code,))


class OwTekstdeel(BaseOwObject):
    source_uuid: str
    source_code: str
    idealization: str
    text_ref: WidRefUnion
    location_refs: List[LocationRefUnion] = Field(default_factory=list)
    gebiedsaanwijzing_refs: List[GebiedsaanwijzingRefUnion] = Field(default_factory=list)

    def __hash__(self):
        return hash((self.source_code,))


class OwState(BaseModel):
    ambtsgebieden: List[OwAmbtsgebied] = Field(default_factory=list)
    regelingsgebieden: List[OwRegelingsgebied] = Field(default_factory=list)
    gebieden: List[OwGebied] = Field(default_factory=list)
    gebiedengroepen: List[OwGebiedengroep] = Field(default_factory=list)
    gebiedsaanwijzingen: List[OwGebiedsaanwijzing] = Field(default_factory=list)
    divisies: List[OwDivisie] = Field(default_factory=list)
    divisieteksten: List[OwDivisietekst] = Field(default_factory=list)
    tekstdelen: List[OwTekstdeel] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


# Acts
class ActiveAct(BaseModel):
    Act_Frbr: Frbr
    Bill_Frbr: Frbr
    Consolidation_Purpose: Purpose
    Document_Type: str
    Procedure_Type: str
    # @todo; data from state upgrade is not correct
    Gios: Dict[str, Gio] = Field(default_factory=dict)
    Gebiedengroepen: Dict[str, Gebiedengroep] = Field(default_factory=dict)
    Gebiedsaanwijzingen: Dict[str, Gebiedsaanwijzing] = Field(default_factory=dict)
    Documents: Dict[int, Document] = Field(default_factory=dict)
    Assets: Dict[str, Asset] = Field(default_factory=dict)
    Wid_Data: WidData
    Ow_State: OwState
    Act_Text: str
    Publication_Version_UUID: str
    model_config = ConfigDict(from_attributes=True)


class ActiveAnnouncement(BaseModel):
    Doc_Frbr: Frbr
    About_Act_Frbr: Frbr
    About_Bill_Frbr: Frbr
    Document_Type: str
    Procedure_Type: str
