from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel

from .relationships import GebruikerInline, RelatedBeleidskeuze


# Shared properties
class BeleidsregelBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Weblink: Optional[str] = None
    Externe_URL: Optional[str] = None


class BeleidsregelCreate(BeleidsregelBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class BeleidsregelUpdate(BeleidsregelBase):
    pass


class BeleidsregelInDBBase(BeleidsregelBase):
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
class Beleidsregel(BeleidsregelInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline
    Beleidskeuzes: List[RelatedBeleidskeuze]


# Properties properties stored in DB
class BeleidsregelInDB(BeleidsregelInDBBase):
    pass
