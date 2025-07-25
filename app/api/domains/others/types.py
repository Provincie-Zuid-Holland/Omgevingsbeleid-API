import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StorageFileBasic(BaseModel):
    UUID: uuid.UUID
    Checksum: str
    Filename: str
    Content_Type: str
    Size: int
    Created_Date: datetime
    Created_By_UUID: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class GraphEdgeType(str, Enum):
    relation = "relation"
    acknowledged_relation = "acknowledged_relation"


class GraphEdge(BaseModel):
    Vertice_A_Code: str
    Vertice_B_Code: str
    Type: GraphEdgeType

    def __hash__(self):
        return hash((self.Vertice_A_Code, self.Vertice_B_Code))

    def __eq__(self, other):
        if not isinstance(other, GraphEdge):
            return False

        return self.Vertice_A_Code == other.Vertice_A_Code and self.Vertice_B_Code == other.Vertice_B_Code


class GraphVertice(BaseModel):
    UUID: uuid.UUID
    Object_Type: str
    Object_ID: int
    Code: str
    Title: str

    @field_validator("Title", mode="before")
    def default_empty_string(cls, v):
        return v or ""

    model_config = ConfigDict(from_attributes=True, validate_assignment=True)


class GraphResponse(BaseModel):
    Vertices: List[GraphVertice]
    Edges: List[GraphEdge]


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
