from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import GebruikerInline, strip_UUID, valid_ref_alias
from app.schemas.reference import BeleidskeuzeReference


class BeleidsprestatieBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Weblink: Optional[str] = None


class BeleidsprestatieCreate(BeleidsprestatieBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class BeleidsprestatieUpdate(BeleidsprestatieCreate):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]


class BeleidsprestatieInDBBase(BeleidsprestatieBase):
    ID: int
    UUID: str

    Created_Date: datetime
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class BeleidsprestatieInDB(BeleidsprestatieInDBBase):
    Created_By: str
    Modified_By: str


class BeleidsprestatieInline(BeleidsprestatieInDBBase):
    Created_By_UUID: str
    Modified_By_UUID: str

    class Config:
        allow_population_by_field_name = True
        alias_generator = strip_UUID


class Beleidsprestatie(BeleidsprestatieInDBBase):
    """
    Full Beleidsprestatie object schema with serialized
    many to many relationships.
    """

    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Valid_Beleidskeuzes: List[BeleidskeuzeReference]

    class Config:
        allow_population_by_field_name = True
        alias_generator = valid_ref_alias
