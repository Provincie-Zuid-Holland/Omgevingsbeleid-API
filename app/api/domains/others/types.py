import hashlib
import re
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional, Any, Generic

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.api.domains.modules.types import TModel


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
    hierarchy_code = "hierarchy_code"


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


class SearchObject(ValidSearchObject, Generic[TModel]):
    Module_ID: Optional[int] = None
    Model: TModel

    model_config = ConfigDict(from_attributes=True, title="SearchObject")


class SearchRequestData(BaseModel):
    Object_Types: Optional[List[str]] = None
    Like: bool = Field(False)


class FileData(BaseModel):
    File: UploadFile

    def __init__(self, /, **data: Any):
        super().__init__(**data)
        self._binary = self.File.file.read()
        self._checksum = hashlib.sha256(self._binary).hexdigest()

    def get_binary(self) -> bytes:
        return self._binary

    def get_checksum(self) -> str:
        return self._checksum

    def get_content_type(self) -> Optional[str]:
        return self.File.content_type

    def get_size(self) -> int:
        return len(self._binary)

    def get_lookup(self) -> str:
        return self._checksum[0:10]

    def normalize_filename(self) -> str:
        normalized_filename = self.File.filename.lower()

        normalized_filename = re.sub(r"[^a-z0-9.]", "-", normalized_filename)
        normalized_filename = re.sub(r"-+", "-", normalized_filename)
        normalized_filename = normalized_filename.strip("-")
        return normalized_filename
