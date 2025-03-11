import uuid
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ValidSearchConfig(BaseModel):
    searchable_columns_high: List[str]
    searchable_columns_low: List[str]
    allowed_object_types: List[str]


class ValidSearchObject(BaseModel):
    UUID: uuid.UUID
    Object_Type: str
    Object_ID: int
    Object_Code: str
    Title: str
    Description: str
    Score: float

    @model_validator(mode="before")
    def generate_object_code(cls, data):
        data["Object_Code"] = f"{data['Object_Type']}-{data['Object_ID']}"
        return data

    @field_validator("Title", "Description", mode="before")
    def default_empty_string(cls, v):
        return v or ""

    model_config = ConfigDict(validate_assignment=True)


class SearchConfig(ValidSearchConfig):
    pass


class SearchObject(ValidSearchObject):
    Module_ID: Optional[int] = None


class SearchRequestData(BaseModel):
    Object_Types: Optional[List[str]] = None
    Like: bool = Field(False)
