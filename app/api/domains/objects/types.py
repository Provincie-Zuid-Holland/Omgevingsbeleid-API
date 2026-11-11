import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator


class ObjectCount(BaseModel):
    object_type: str
    count: int

    model_config = ConfigDict(from_attributes=True)


# Wraps a List type to a Pydantic model type for FastAPI
ObjectCountResponse = RootModel[list[ObjectCount]]


class WriteRelation(BaseModel):
    object_id: int
    object_type: str
    description: str = Field("")

    @field_validator("description", mode="before")
    def default_empty_string(cls, v):
        return v or ""

    @property
    def code(self) -> str:
        return f"{self.object_type}-{self.object_id}"


class ReadRelationShort(BaseModel):
    object_id: int
    object_type: str
    description: str = Field("")

    @field_validator("description", mode="before")
    def default_empty_string(cls, v):
        return v or ""

    @property
    def code(self) -> str:
        return f"{self.object_type}-{self.object_id}"


class ReadRelation(BaseModel):
    object_id: int
    object_type: str
    description: str = Field("")
    title: str = Field("")

    @field_validator("description", "title", mode="before")
    def default_empty_string(cls, v):
        return v or ""

    @property
    def code(self) -> str:
        return f"{self.object_type}-{self.object_id}"


class ObjectStatics(BaseModel):
    object_type: str
    object_id: int
    code: str
    cached_title: str

    @field_validator("cached_title", mode="before")
    def default_empty_string(cls, v):
        return "" if v is None else v

    model_config = ConfigDict(from_attributes=True)


class HierarchyStatics(ObjectStatics):
    pass


class FilterObjectCode(BaseModel):
    object_type: str
    lineage_id: int

    def get_code(self) -> str:
        return f"{self.object_type}-{self.lineage_id}"


class NextObjectVersion(BaseModel):
    id: uuid.UUID
    title: str
    start_validity: datetime
    end_validity: datetime | None = None
    created_date: datetime
    modified_date: datetime
    previous_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
