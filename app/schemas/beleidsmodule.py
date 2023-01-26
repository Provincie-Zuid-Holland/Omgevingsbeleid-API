from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import GebruikerInline
from app.schemas.reference import GenericReferenceUpdate
from app.schemas.related import RelatedBeleidskeuze, RelatedMaatregel


class BeleidsmoduleBase(BaseModel):
    Titel: Optional[str] = None
    Besluit_Datum: Optional[str] = None


class BeleidsmoduleCreate(BeleidsmoduleBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    Beleidskeuzes: Optional[List[GenericReferenceUpdate]]
    Maatregelen: Optional[List[GenericReferenceUpdate]]


class BeleidsmoduleUpdate(BeleidsmoduleBase):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]

    Beleidskeuzes: Optional[List[GenericReferenceUpdate]]
    Maatregelen: Optional[List[GenericReferenceUpdate]]


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


class Beleidsmodule(BeleidsmoduleInDBBase):
    """
    Full Beleidsmodule object schema with serialized
    many to many relationships.
    """

    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Beleidskeuzes: List[RelatedBeleidskeuze]
    Maatregelen: List[RelatedMaatregel]

    class Config:
        allow_population_by_field_name = True


class BeleidsmoduleInDB(BeleidsmoduleInDBBase):
    pass
