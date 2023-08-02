import uuid
from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel


class Werkingsgebied(BaseModel):
    ID: int
    UUID: uuid.UUID
    Created_Date: datetime
    Modified_Date: datetime
    Title: str

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class GeoSearchResult(BaseModel):
    UUID: Union[str, uuid.UUID]
    Gebied: Union[str, uuid.UUID]
    Type: str
    Titel: Optional[str]
    Omschrijving: Optional[str]


# TODO: Remove, changed to PagedResponse
class SearchResultWrapper(BaseModel):
    total: int = 0
    results: List[GeoSearchResult] = []
