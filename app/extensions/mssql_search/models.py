import uuid
from typing import List, Optional

from pydantic import BaseModel, validator


class ValidSearchConfig(BaseModel):
    searchable_columns_high: List[str]
    searchable_columns_low: List[str]
    allowed_object_types: List[str]


class ValidSearchObject(BaseModel):
    UUID: uuid.UUID
    Object_Type: str
    Object_ID: int
    Title: str
    Description: str
    Score: float

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
