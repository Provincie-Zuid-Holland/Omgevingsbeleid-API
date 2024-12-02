import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field


class Werkingsgebied(BaseModel):
    ID: Optional[int]
    UUID: uuid.UUID
    Created_Date: datetime
    Modified_Date: datetime
    Title: str
    Start_Validity: Optional[datetime] = Field(None)
    End_Validity: Optional[datetime] = Field(None)
    Geometry_Hash: Optional[str] = Field(None)

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
