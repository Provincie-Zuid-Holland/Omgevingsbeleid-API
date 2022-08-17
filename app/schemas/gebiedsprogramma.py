from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from .relationships import GebruikerInline, RelatedMaatregel

from app.util.legacy_helpers import to_ref_field


# Shared properties
class GebiedsprogrammaBase(BaseModel):
    Status: Optional[str] = None
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Afbeelding: Optional[str] = None


class GebiedsprogrammaCreate(GebiedsprogrammaBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class GebiedsprogrammaUpdate(GebiedsprogrammaBase):
    pass


class GebiedsprogrammaInDBBase(GebiedsprogrammaBase):
    ID: int
    UUID: str

    Created_By: str
    Created_Date: datetime
    Modified_By: str
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    Status: str
    Titel: str
    Omschrijving: str
    Afbeelding: str

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


# Properties to return to client
class Gebiedsprogramma(GebiedsprogrammaInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Maatregelen: List[RelatedMaatregel]

    class Config:
        allow_population_by_field_name = True
        alias_generator = to_ref_field


# Properties properties stored in DB
class GebiedsprogrammaInDB(GebiedsprogrammaInDBBase):
    pass
