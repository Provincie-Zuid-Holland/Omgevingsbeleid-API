from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import BeleidskeuzeReference, GebruikerInline, valid_ref_alias


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

    Created_By: str
    Created_Date: datetime
    Modified_By: str
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class Belang(BelangInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Valid_Beleidskeuzes: List[BeleidskeuzeReference]

    class Config:
        allow_population_by_field_name = True
        alias_generator = valid_ref_alias


# Properties properties stored in DB
class BelangInDB(BelangInDBBase):
    pass
