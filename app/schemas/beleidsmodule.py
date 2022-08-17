from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .relationships import GebruikerInline, RelatedBeleidskeuze, RelatedMaatregel
from app.core.config import settings


# Shared properties
class BeleidsmoduleBase(BaseModel):
    Titel: Optional[str] = None
    Besluit_Datum: datetime = Field(default=settings.MIN_DATETIME)


class BeleidsmoduleCreate(BeleidsmoduleBase):
    Begin_Geldigheid: datetime = Field(default=settings.MIN_DATETIME)
    Eind_Geldigheid: datetime = Field(default=settings.MIN_DATETIME)


class BeleidsmoduleUpdate(BeleidsmoduleBase):
    pass


class BeleidsmoduleInDBBase(BeleidsmoduleBase):
    ID: int
    UUID: str

    Created_By: str
    Created_Date: datetime
    Modified_By: str
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    Titel: str
    Besluit_Datum: datetime

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


# Properties to return to client
class Beleidsmodule(BeleidsmoduleInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Beleidskeuzes: List[RelatedBeleidskeuze]
    Maatregelen: List[RelatedMaatregel]

    class Config:
        allow_population_by_field_name = True


# Properties properties stored in DB
class BeleidsmoduleInDB(BeleidsmoduleInDBBase):
    pass
