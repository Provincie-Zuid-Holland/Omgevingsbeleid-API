import uuid
from typing import List, Optional

from pydantic import BaseModel, Field, root_validator, validator


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

    @root_validator(pre=True)
    def generate_object_code(cls, values):
        values["Object_Code"] = f"{values['Object_Type']}-{values['Object_ID']}"
        return values

    @validator("Title", "Description", pre=True)
    def default_empty_string(cls, v):
        return v or ""

    class Config:
        validate_assignment = True


class SearchConfig(ValidSearchConfig):
    pass


class SearchObject(ValidSearchObject):
    Module_ID: Optional[int]


class SearchRequestData(BaseModel):
    Object_Types: Optional[List[str]]
    Like: bool = Field(False)
