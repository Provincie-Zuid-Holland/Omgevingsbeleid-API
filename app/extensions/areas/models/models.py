import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, validator


class AreaBasic(BaseModel):
    UUID: uuid.UUID
    Created_Date: datetime
    Created_By_UUID: uuid.UUID
    Source_UUID: uuid.UUID
    Source_Title: str
    Source_Modified_Date: datetime

    class Config:
        orm_mode = True


class WerkingsgebiedStatics(BaseModel):
    Object_Type: str
    Object_ID: int
    Code: str
    Cached_Title: str

    @validator("Cached_Title", pre=True)
    def default_empty_string(cls, v):
        return "" if v is None else v

    class Config:
        orm_mode = True


class GeoSearchResult(BaseModel):
    UUID: str
    Object_Type: str
    Titel: Optional[str]
    Omschrijving: Optional[str]

    @validator("UUID", pre=True)
    def convert_uuid_to_str(cls, v):
        return str(v)


class SearchResultWrapper(BaseModel):
    Total: int = 0
    Results: List[GeoSearchResult] = []


class GeometryFunctions(str, Enum):
    # Determines if the geometry is entirely contained within the Werkingsgebied.
    CONTAINS = "CONTAINS"
    # It's the inverse of Contains. It determines the Werkingsgebied is entirely within the given geometry
    WITHIN = "WITHIN"
    # Determines in the geometry and Werkingsgebied overlap
    OVERLAPS = "OVERLAPS"
    # If a geometry instance intersects another geometry instance
    INTERSECTS = "INTERSECTS"


VALID_GEOMETRIES = ["Polygon", "Point"]
