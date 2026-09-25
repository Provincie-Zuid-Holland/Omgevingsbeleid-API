import hashlib
import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict, field_validator


class StorageFileBasic(BaseModel):
    id: uuid.UUID
    checksum: str
    filename: str
    content_type: str
    size: int
    created_date: datetime
    created_by_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class GraphEdgeType(str, Enum):
    relation = "relation"
    acknowledged_relation = "acknowledged_relation"
    hierarchy_code = "hierarchy_code"


class GraphEdge(BaseModel):
    vertice_a_code: str
    vertice_b_code: str
    type: GraphEdgeType

    def __hash__(self):
        return hash((self.vertice_a_code, self.vertice_b_code))

    def __eq__(self, other):
        if not isinstance(other, GraphEdge):
            return False

        return self.vertice_a_code == other.vertice_a_code and self.vertice_b_code == other.vertice_b_code


class GraphVertice(BaseModel):
    id: uuid.UUID
    object_type: str
    object_id: int
    code: str
    title: str

    @field_validator("title", mode="before")
    def default_empty_string(cls, v):
        return v or ""

    model_config = ConfigDict(from_attributes=True, validate_assignment=True)


class GraphResponse(BaseModel):
    vertices: list[GraphVertice]
    edges: list[GraphEdge]


class ObjectRelatedFileResponse(BaseModel):
    id: uuid.UUID
    code: str
    file_id: uuid.UUID
    title: str
    created_date: datetime
    created_by_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


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

    def get_content_type(self) -> str | None:
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


class Hoofdlijn(BaseModel):
    id: uuid.UUID
    name: str
    type: str

    model_config = ConfigDict(from_attributes=True)
