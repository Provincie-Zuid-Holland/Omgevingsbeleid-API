from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime

from .gebruiker import GebruikerInline


# class BeleidskeuzeShortInline(BaseModel):
#     ID: int
#     UUID: str
#     Titel: str

#     class Config:
#         orm_mode = True
#         arbitrary_types_allowed = True


# Shared properties
class AmbitieBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Weblink: Optional[str] = None


class AmbitieCreate(AmbitieBase):
    pass


class AmbitieUpdate(AmbitieBase):
    pass


class AmbitieInDBBase(AmbitieBase):
    ID: int
    UUID: str

    Created_By: GebruikerInline
    Created_Date: datetime
    Modified_By: GebruikerInline
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    Titel: str
    Omschrijving: str
    Weblink: str
    # Beleidskeuzes: List[BeleidskeuzeShortInline]

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


# Properties to return to client
class Ambitie(AmbitieInDBBase):
    pass


# Properties properties stored in DB
class AmbitieInDB(AmbitieInDBBase):
    pass
