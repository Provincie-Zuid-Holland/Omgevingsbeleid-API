from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from .relationships import (
    GebruikerInline,
    RelatedBeleidskeuze,
    WerkingsgebiedShortInline,
)

from app.util.legacy_helpers import to_ref_field


# Shared properties
class VerordeningBase(BaseModel):
    Titel: Optional[str] = None
    Inhoud: Optional[str] = None
    Weblink: Optional[str] = None
    Status: Optional[str] = None
    Type: Optional[str] = None
    Gebied_UUID: Optional[str] = None
    Volgnummer: Optional[str] = None


class VerordeningCreate(VerordeningBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class VerordeningUpdate(VerordeningBase):
    pass


class VerordeningInDBBase(VerordeningBase):
    ID: int
    UUID: str

    Created_By: str
    Created_Date: datetime
    Modified_By: str
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


# Properties to return to client
class Verordening(VerordeningInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Portefeuillehouder_1: GebruikerInline
    Portefeuillehouder_2: GebruikerInline
    Eigenaar_1: GebruikerInline
    Eigenaar_2: GebruikerInline
    Opdrachtgever: GebruikerInline
    Gebied: WerkingsgebiedShortInline

    Beleidskeuzes: List[RelatedBeleidskeuze]

    class Config:
        allow_population_by_field_name = True
        alias_generator = to_ref_field


# Properties properties stored in DB
class VerordeningInDB(VerordeningInDBBase):
    pass
