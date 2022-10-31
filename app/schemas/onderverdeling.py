from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel

from app.schemas.common import GebruikerInline
from app.util.legacy_helpers import to_ref_field


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


class Onderverdeling(OnderverdelingInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    class Config:
        allow_population_by_field_name = True
        alias_generator = to_ref_field


class OnderverdelingInDB(OnderverdelingInDBBase):
    pass
