import uuid
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


class Location(BaseModel):
    UUID: str
    Identifier: str  # basisgeo:id - also used in ow
    Gml_ID: str
    Group_ID: str
    Title: str


class Werkingsgebied(BaseModel):
    UUID: str
    Identifier: str
    Hash: str
    Object_ID: int
    Title: str
    Owner_Act: str
    Frbr: Frbr
    Locations: List[Location]

    def is_still_valid(self) -> bool:
        try:
            # If any of the "ids" are not real uuids, then its the old system which is no longer allowed
            # We will tell that this Werkingsgebied is no longer valid
            # And then we can force a new version, without manually needing to tag all "Werkingsgebieden"
            for location in self.Locations:
                _ = uuid.UUID(location.UUID)
                _ = uuid.UUID(location.Identifier)
                _ = uuid.UUID(location.Gml_ID)
                _ = uuid.UUID(location.Group_ID)
        except ValueError:
            return False
        return True


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
    source_uuid: str
    source_code: str
    title: str
    geometry_ref: str

    def __hash__(self):
        return hash((self.source_code,))


class OwGebiedengroep(BaseOwObject):
    source_uuid: str
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

    def __hash__(self):
        return hash((self.source_code,))


class OwState(BaseModel):
    ambtsgebieden: Set[OwAmbtsgebied] = Field(default_factory=set)
    regelingsgebieden: Set[OwRegelingsgebied] = Field(default_factory=set)
    gebieden: Set[OwGebied] = Field(default_factory=set)
    gebiedengroepen: Set[OwGebiedengroep] = Field(default_factory=set)
    gebiedsaanwijzingen: Set[OwGebiedsaanwijzing] = Field(default_factory=set)
    divisies: Set[OwDivisie] = Field(default_factory=set)
    divisieteksten: Set[OwDivisietekst] = Field(default_factory=set)
    tekstdelen: Set[OwTekstdeel] = Field(default_factory=set)


# Acts
class ActiveAct(BaseModel):
    Act_Frbr: Frbr
    Bill_Frbr: Frbr
    Consolidation_Purpose: Purpose
    Document_Type: str
    Procedure_Type: str
    Werkingsgebieden: Dict[int, Werkingsgebied]
    Documents: Dict[int, Document] = Field({})
    Assets: Dict[str, Asset]
    Wid_Data: WidData
    Ow_State: OwState
    Act_Text: str
    Publication_Version_UUID: str


class ActiveAnnouncement(BaseModel):
    Doc_Frbr: Frbr
    About_Act_Frbr: Frbr
    About_Bill_Frbr: Frbr
    Document_Type: str
    Procedure_Type: str
