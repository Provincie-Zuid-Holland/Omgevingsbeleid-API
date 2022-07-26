from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel
from pydantic.utils import GetterDict

from app.util.legacy_helpers import to_ref_field

from .gebruiker import GebruikerInline


# Shared properties
class OnderverdelingBase(BaseModel):
    Onderverdeling: Optional[str] = None
    Structuur: Optional[str] = None
    symbol: Optional[str] = None
    SHAPE: Optional[str] = None


class OnderverdelingCreate(OnderverdelingBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class OnderverdelingUpdate(OnderverdelingBase):
    pass


class OnderverdelingInDBBase(OnderverdelingBase):
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
class Onderverdeling(OnderverdelingInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    class Config:
        allow_population_by_field_name = True
        alias_generator = to_ref_field


# Properties properties stored in DB
class OnderverdelingInDB(OnderverdelingInDBBase):
    pass
