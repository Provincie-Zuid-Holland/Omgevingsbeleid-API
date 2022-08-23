from abc import ABCMeta
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models import Beleidsdoel_Ambities

from .relationships import (
    AmbitieCreateShortInline,
    GebruikerInline,
    RelatedAmbitie,
    RelatedBeleidskeuze,
)


# Shared properties
class BeleidsdoelBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Weblink: Optional[str] = None


class BeleidsdoelCreateWithoutRelations(BeleidsdoelBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class BeleidsdoelCreateRelations(BaseModel):
    Ambities: List[AmbitieCreateShortInline]

    def add_relations(self, beleidsdoel, session):
        for ambitie in self.Ambities:
            r = Beleidsdoel_Ambities(
                Beleidsdoel=beleidsdoel,
                Ambitie_UUID=ambitie.UUID,
                Koppeling_Omschrijving=ambitie.Koppeling_Omschrijving,
            )
            session.add(r)


class BeleidsdoelCreate(BeleidsdoelBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime
    Ambities: List[AmbitieCreateShortInline]

    def as_create_model(self) -> BeleidsdoelCreateWithoutRelations:
        return BeleidsdoelCreateWithoutRelations(**self.dict())
    
    def as_create_relations(self) -> BeleidsdoelCreateRelations:
        return BeleidsdoelCreateRelations(**self.dict())


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
