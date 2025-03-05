import uuid
from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, field_validator


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
