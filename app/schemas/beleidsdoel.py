from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from app.schemas.beleidsprestatie import BeleidsprestatieInDBBase

from app.schemas.common import GebruikerInline, strip_UUID, valid_ref_alias
from app.schemas.reference import BeleidskeuzeReference
from app.schemas.related import RelatedAmbitie


class BeleidsdoelBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Weblink: Optional[str] = None


class BeleidsdoelCreate(BeleidsdoelBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class BeleidsdoelUpdate(BeleidsdoelCreate):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]


class BeleidsdoelInDBBase(BeleidsdoelBase):
    ID: int
    UUID: str

    Created_Date: datetime
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class BeleidsdoelInDB(BeleidsdoelInDBBase):
    Created_By: str
    Modified_By: str


class BeleidsdoelInline(BeleidsprestatieInDBBase):
    Created_By_UUID: str
    Modified_By_UUID: str

    class Config:
        allow_population_by_field_name = True
        alias_generator = strip_UUID


class Beleidsdoel(BeleidsdoelInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Ambities: List[RelatedAmbitie]

    Valid_Beleidskeuzes: List[BeleidskeuzeReference]

    class Config:
        allow_population_by_field_name = True
        alias_generator = valid_ref_alias
