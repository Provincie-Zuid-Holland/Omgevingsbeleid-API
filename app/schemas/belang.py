from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import GebruikerInline, strip_UUID, valid_ref_alias
from app.schemas.reference import BeleidskeuzeReference


# Shared properties
class BelangBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Weblink: Optional[str] = None
    Type: Optional[str] = None


class BelangCreate(BelangBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class BelangUpdate(BelangCreate):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]


class BelangInDBBase(BelangBase):
    ID: int
    UUID: str

    Created_Date: datetime
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class BelangInDB(BelangInDBBase):
    Created_By: str
    Modified_By: str


class BelangInline(BelangInDBBase):
    Created_By_UUID: str
    Modified_By_UUID: str

    class Config:
        allow_population_by_field_name = True
        alias_generator = strip_UUID


class Belang(BelangInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Valid_Beleidskeuzes: List[BeleidskeuzeReference]

    class Config:
        allow_population_by_field_name = True
        alias_generator = valid_ref_alias
