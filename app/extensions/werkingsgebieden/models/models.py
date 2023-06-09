from datetime import datetime
from typing import List, Union
import uuid
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
    Gebied: str
    Titel: str
    Omschrijving: str
    Type: str
    UUID: str
    RANK: int = 100


class SearchResultWrapper(BaseModel):
    results: List[GeoSearchResult] = []
    total: int = len(results)
