from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from .relationships import GebruikerInline, RelatedAmbitie, RelatedBeleidskeuze
from .ambitie import Ambitie


# Shared properties
class BeleidsdoelBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Weblink: Optional[str] = None


class BeleidsdoelCreate(BeleidsdoelBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime
    Ambities: Optional[List[Ambitie]]


class BeleidsdoelUpdate(BeleidsdoelBase):
    pass


class BeleidsdoelInDBBase(BeleidsdoelBase):
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
class Beleidsdoel(BeleidsdoelInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline
    Beleidskeuzes: List[RelatedBeleidskeuze]
    Ambities: List[RelatedAmbitie]


# Properties properties stored in DB
class BeleidsdoelInDB(BeleidsdoelInDBBase):
    pass
