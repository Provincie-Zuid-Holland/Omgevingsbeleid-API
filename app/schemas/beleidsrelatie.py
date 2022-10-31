from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel
from pydantic.utils import GetterDict

from app.schemas.common import BeleidskeuzeShortInline, GebruikerInline

from .beleidskeuze import BeleidskeuzeInDB


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


class Beleidsrelatie(BeleidsrelatieInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Van_Beleidskeuze: BeleidskeuzeShortInline
    Naar_Beleidskeuze: BeleidskeuzeShortInline


class BeleidsrelatieInDB(BeleidsrelatieInDBBase):
    pass
