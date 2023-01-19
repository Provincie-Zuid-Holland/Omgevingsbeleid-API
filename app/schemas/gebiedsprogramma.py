from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import (
    BeleidsmoduleReference,
    GebruikerInline,
    RelatedMaatregel,
    valid_ref_alias,
)


class GebiedsprogrammaBase(BaseModel):
    Status: Optional[str] = None
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Weblink: Optional[str] = None
    Besluitnummer: Optional[str] = None
    Afbeelding: Optional[str] = None


class GebiedsprogrammaCreate(GebiedsprogrammaBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class GebiedsprogrammaUpdate(GebiedsprogrammaCreate):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]


class GebiedsprogrammaInDBBase(GebiedsprogrammaBase):
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


class GebiedsprogrammaInDB(GebiedsprogrammaInDBBase):
    pass


class Gebiedsprogramma(GebiedsprogrammaInDBBase):
    """
    Full Gebiedsprogramma object schema with serialized
    many to many relationships.
    """

    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Valid_Maatregelen: List[RelatedMaatregel]

    # Refs
    Beleidsmodules: List[BeleidsmoduleReference]

    class Config:
        allow_population_by_field_name = True
        alias_generator = valid_ref_alias
