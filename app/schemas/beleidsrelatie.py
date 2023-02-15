from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.base import RelatieStatus as StatusEnum
from app.schemas.beleidskeuze import Beleidskeuze
from app.schemas.common import GebruikerInline


# Shared properties
class BeleidsrelatieBase(BaseModel):
    Status: Optional[StatusEnum]
    Omschrijving: Optional[str]
    Aanvraag_Datum: Optional[datetime]
    Datum_Akkoord: Optional[datetime]


class BeleidsrelatieCreate(BeleidsrelatieBase):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]

    Van_Beleidskeuze_UUID: str
    Naar_Beleidskeuze_UUID: str


class BeleidsrelatieUpdate(BeleidsrelatieCreate):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]

    Status: Optional[StatusEnum]

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


class BeleidsrelatieInDB(BeleidsrelatieInDBBase):
    pass


class Beleidsrelatie(BeleidsrelatieInDBBase):
    Created_Date: Optional[datetime]
    Created_By: Optional[GebruikerInline]

    Modified_Date: Optional[datetime]
    Modified_By: Optional[GebruikerInline]

    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]

    Van_Beleidskeuze: Beleidskeuze
    Naar_Beleidskeuze: Beleidskeuze
