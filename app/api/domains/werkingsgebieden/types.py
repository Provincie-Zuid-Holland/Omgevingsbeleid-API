import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AreaBasic(BaseModel):
    UUID: uuid.UUID
    Created_Date: datetime
    Created_By_UUID: uuid.UUID
    Source_UUID: uuid.UUID
    Source_Title: str
    Source_Modified_Date: datetime

    model_config = ConfigDict(from_attributes=True)


class WerkingsgebiedStatics(BaseModel):
    Object_Type: str
    Object_ID: int
    Code: str
    Cached_Title: str

    @field_validator("Cached_Title", mode="before")
    def default_empty_string(cls, v):
        return "" if v is None else v

    model_config = ConfigDict(from_attributes=True)


class GeoSearchResult(BaseModel):
    UUID: str
    Area_UUID: Optional[str] = None
    Object_Type: str
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None

    @field_validator("UUID", "Area_UUID", mode="before")
    def convert_uuid_to_str(cls, v):
        return str(v)


class SearchResultWrapper(BaseModel):
    Total: int = 0
    Results: List[GeoSearchResult] = Field(default_factory=list)


class Werkingsgebied(BaseModel):
    ID: Optional[int] = None
    UUID: uuid.UUID
    Created_Date: datetime
    Modified_Date: datetime
    Title: str
    Start_Validity: Optional[datetime] = Field(None)
    End_Validity: Optional[datetime] = Field(None)
    Geometry_Hash: Optional[str] = Field(None)
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
