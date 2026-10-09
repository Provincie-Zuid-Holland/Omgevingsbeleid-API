import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.utils.pagination import OrderConfig, SortOrder


class AreaBasic(BaseModel):
    id: uuid.UUID
    created_date: datetime
    created_by_id: uuid.UUID
    source_id: uuid.UUID
    source_title: str
    source_created_date: datetime

    model_config = ConfigDict(from_attributes=True)


class WerkingsgebiedStatics(BaseModel):
    object_type: str
    object_id: int
    code: str
    cached_title: str

    @field_validator("cached_title", mode="before")
    def default_empty_string(cls, v):
        return "" if v is None else v

    model_config = ConfigDict(from_attributes=True)


class Werkingsgebied(BaseModel):
    id: uuid.UUID
    ref_id: int | None = None
    created_date: datetime
    modified_date: datetime
    title: str
    geometry_hash: str | None = Field(None)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class InputGeoWerkingsgebiedenSortColumn(str, Enum):
    title = "title"
    created_date = "created_date"


input_geo_werkingsgebieden_order_config = OrderConfig(
    default_column=InputGeoWerkingsgebiedenSortColumn.created_date.value,
    default_order=SortOrder.DESC,
    allowed_columns=[col.value for col in InputGeoWerkingsgebiedenSortColumn],
)


class InputGeoOnderverdeling(BaseModel):
    id: uuid.UUID
    created_date: datetime
    title: str
    description: str
    geometry_hash: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class InputGeoWerkingsgebied(BaseModel):
    id: uuid.UUID
    created_date: datetime
    title: str
    description: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class InputGeoWerkingsgebiedDetailed(BaseModel):
    id: uuid.UUID
    created_date: datetime
    title: str
    description: str
    onderverdelingen: list[InputGeoOnderverdeling]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
