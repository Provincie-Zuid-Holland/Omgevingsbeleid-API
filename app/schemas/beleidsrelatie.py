from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from app.schemas.beleidskeuze import Beleidskeuze

from app.schemas.common import (
    GebruikerInline,
)


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

    Van_Beleidskeuze_UUID: str
    Naar_Beleidskeuze_UUID: str


class BeleidsrelatieUpdate(BeleidsrelatieCreate):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]

    Van_Beleidskeuze_UUID: Optional[str]
    Naar_Beleidskeuze_UUID: Optional[str]


class BeleidsrelatieInDBBase(BeleidsrelatieBase):
    ID: int
    UUID: str

    Created_By: str
    Created_Date: datetime
    Modified_By: str
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime
    Van_Beleidskeuze: str
    Naar_Beleidskeuze: str

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class Beleidsrelatie(BeleidsrelatieInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Van_Beleidskeuze: Beleidskeuze
    Naar_Beleidskeuze: Beleidskeuze


class BeleidsrelatieInDB(BeleidsrelatieInDBBase):
    pass
