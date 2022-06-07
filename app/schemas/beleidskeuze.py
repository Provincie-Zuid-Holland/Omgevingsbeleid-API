from optparse import Option
from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime

from .gebruiker import GebruikerInline


# Shared properties
class BeleidskeuzeBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving_Keuze: Optional[str] = None
    Omschrijving_Werking: Optional[str] = None
    Provinciaal_Belang: Optional[str] = None
    Aanleiding: Optional[str] = None
    Afweging: Optional[str] = None
    Besluitnummer: Optional[str] = None
    Tags: Optional[str] = None
    Status: Optional[str] = None
    Weblink: Optional[str] = None


class BeleidskeuzeCreate(BeleidskeuzeBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class BeleidskeuzeUpdate(BeleidskeuzeBase):
    pass


class BeleidskeuzeInDBBase(BeleidskeuzeBase):
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
class Beleidskeuze(BeleidskeuzeInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline
    pass


# Properties properties stored in DB
class BeleidskeuzeInDB(BeleidskeuzeInDBBase):
    pass

