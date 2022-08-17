from typing import Optional
from datetime import datetime

from pydantic import BaseModel

from .relationships import BeleidskeuzeShortInline, GebruikerInline


# Shared properties
class BeleidsrelatieBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Status: Optional[str] = None
    Aanvraag_Datum = datetime
    Datum_Akkoord = datetime


class BeleidsrelatieCreate(BeleidsrelatieBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class BeleidsrelatieUpdate(BeleidsrelatieBase):
    pass


class BeleidsrelatieInDBBase(BeleidsrelatieBase):
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
class Beleidsrelatie(BeleidsrelatieInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Van_Beleidskeuze: BeleidskeuzeShortInline
    Naar_Beleidskeuze: BeleidskeuzeShortInline


# Properties properties stored in DB
class BeleidsrelatieInDB(BeleidsrelatieInDBBase):
    pass
