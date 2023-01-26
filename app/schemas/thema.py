from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import GebruikerInline, strip_UUID, valid_ref_alias
from app.schemas.related import RelatedBeleidskeuze


class ThemaBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Weblink: Optional[str] = None


class ThemaCreate(ThemaBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class ThemaUpdate(ThemaBase):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]


class ThemaInDBBase(ThemaBase):
    ID: int
    UUID: str

    Created_Date: datetime
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class ThemaInDB(ThemaInDBBase):
    Created_By: str
    Modified_By: str


class ThemaInline(ThemaInDBBase):
    Created_By_UUID: str
    Modified_By_UUID: str

    class Config:
        allow_population_by_field_name = True
        alias_generator = strip_UUID


# Properties to return to client
class Thema(ThemaInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Valid_Beleidskeuzes: List[RelatedBeleidskeuze]

    class Config:
        allow_population_by_field_name = True
        alias_generator = valid_ref_alias
