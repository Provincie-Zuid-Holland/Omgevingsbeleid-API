from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from .relationships import GebruikerInline, RelatedBeleidskeuze
from app.util.legacy_helpers import to_ref_field


# Shared properties
class BelangBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Status: Optional[str] = None
    Weblink: Optional[str] = None
    Type: Optional[str] = None


class BelangCreate(BelangBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class BelangUpdate(BelangBase):
    pass


class BelangInDBBase(BelangBase):
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
class Belang(BelangInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Beleidskeuzes: List[RelatedBeleidskeuze]

    class Config:
        allow_population_by_field_name = True
        alias_generator = to_ref_field


# Properties properties stored in DB
class BelangInDB(BelangInDBBase):
    pass
