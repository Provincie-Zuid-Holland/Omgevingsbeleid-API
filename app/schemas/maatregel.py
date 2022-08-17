from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from .relationships import (
    GebruikerInline,
    RelatedBeleidskeuze,
    RelatedBeleidsmodule,
    RelatedGebiedsprogramma,
)
from app.util.legacy_helpers import to_ref_field


class MaatregelBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Toelichting: Optional[str] = None
    Toelichting_Raw: Optional[str] = None
    Weblink: Optional[str] = None
    Status: Optional[str] = None
    Gebied_Duiding: Optional[str] = None
    Tags: Optional[str] = None


class MaatregelCreate(MaatregelBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class MaatregelUpdate(MaatregelBase):
    pass


class MaatregelInDBBase(MaatregelBase):
    ID: int
    UUID: str

    Created_By: str
    Created_Date: datetime
    Modified_By: str
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    Titel: str
    Omschrijving: str
    Toelichting: str
    Toelichting_Raw: str
    Weblink: str
    Status: str
    Gebied_Duiding: str
    Tags: str

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


# Properties to return to client
class Maatregel(MaatregelInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Beleidskeuzes: List[RelatedBeleidskeuze]
    Beleidsmodules: List[RelatedBeleidsmodule]
    Gebiedsprogrammas: List[RelatedGebiedsprogramma]

    # Aanpassing Op
    # Eigenaar
    # Portefeuillehouder
    # Opdrachtgever
    # Gebied

    class Config:
        allow_population_by_field_name = True
        alias_generator = to_ref_field


# Properties properties stored in DB
class MaatregelInDB(MaatregelInDBBase):
    pass
