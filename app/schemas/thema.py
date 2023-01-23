from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import GebruikerInline, RelatedBeleidskeuze, valid_ref_alias

# Shared properties
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
class Thema(ThemaInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Valid_Beleidskeuzes: List[RelatedBeleidskeuze]

    class Config:
        allow_population_by_field_name = True
        alias_generator = valid_ref_alias


# Properties properties stored in DB
class ThemaInDB(ThemaInDBBase):
    pass
