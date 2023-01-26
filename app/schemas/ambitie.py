from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import GebruikerInline, strip_UUID, valid_ref_alias
from app.schemas.reference import BeleidsdoelReference


class AmbitieBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Weblink: Optional[str] = None


class AmbitieCreate(AmbitieBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class AmbitieUpdate(AmbitieCreate):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]


class AmbitieInDBBase(AmbitieBase):
    ID: int
    UUID: str

    Created_Date: datetime
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class AmbitieInDB(AmbitieInDBBase):
    Created_By: str
    Modified_By: str


class AmbitieInline(AmbitieInDBBase):
    Created_By_UUID: str
    Modified_By_UUID: str

    class Config:
        allow_population_by_field_name = True
        alias_generator = strip_UUID


class Ambitie(AmbitieInDBBase):
    """
    Full Ambitie object schema with serialized
    many to many relationships.
    """

    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Valid_Beleidsdoelen: List[BeleidsdoelReference]

    class Config:
        allow_population_by_field_name = True
        alias_generator = valid_ref_alias
