from enum import Enum
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.utils.pagination import OrderConfig, SortOrder


class AreaBasic(BaseModel):
    UUID: uuid.UUID
    Created_Date: datetime
    Created_By_UUID: uuid.UUID
    Source_UUID: uuid.UUID
    Source_Title: str
    Source_Created_Date: datetime

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


class InputGeoWerkingsgebiedenSortColumn(str, Enum):
    Title = "Title"
    Created_Date = "Created_Date"


input_geo_werkingsgebieden_order_config = OrderConfig(
    default_column=InputGeoWerkingsgebiedenSortColumn.Created_Date.value,
    default_order=SortOrder.DESC,
    allowed_columns=[col.value for col in InputGeoWerkingsgebiedenSortColumn],
)


class InputGeoOnderverdeling(BaseModel):
    UUID: uuid.UUID
    Created_Date: datetime
    Title: str
    Description: str
    Geometry_Hash: str
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class InputGeoWerkingsgebied(BaseModel):
    UUID: uuid.UUID
    Created_Date: datetime
    Title: str
    Description: str
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class InputGeoWerkingsgebiedDetailed(BaseModel):
    UUID: uuid.UUID
    Created_Date: datetime
    Title: str
    Description: str
    Onderverdelingen: List[InputGeoOnderverdeling]
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
