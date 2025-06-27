import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator


class ObjectCount(BaseModel):
    object_type: str
    count: int

    model_config = ConfigDict(from_attributes=True)


# Wraps a List type to a Pyndantic model type for FastAPI
ObjectCountResponse = RootModel[List[ObjectCount]]


class WriteRelation(BaseModel):
    Object_ID: int
    Object_Type: str
    Description: str = Field("")

    @field_validator("Description", mode="before")
    def default_empty_string(cls, v):
        return v or ""

    @property
    def Code(self) -> str:
        return f"{self.Object_Type}-{self.Object_ID}"


class ReadRelationShort(BaseModel):
    Object_ID: int
    Object_Type: str
    Description: str = Field("")

    @field_validator("Description", mode="before")
    def default_empty_string(cls, v):
        return v or ""

    @property
    def Code(self) -> str:
        return f"{self.Object_Type}-{self.Object_ID}"


class ReadRelation(BaseModel):
    Object_ID: int
    Object_Type: str
    Description: str = Field("")
    Title: str = Field("")

    @field_validator("Description", "Title", mode="before")
    def default_empty_string(cls, v):
        return v or ""

    @property
    def Code(self) -> str:
        return f"{self.Object_Type}-{self.Object_ID}"


class HierarchyStatics(BaseModel):
    Object_Type: str
    Object_ID: int
    Code: str
    Cached_Title: str

    @field_validator("Cached_Title", mode="before")
    def default_empty_string(cls, v):
        return "" if v is None else v

    model_config = ConfigDict(from_attributes=True)


class FilterObjectCode(BaseModel):
    object_type: str
    lineage_id: int

    def get_code(self) -> str:
        return f"{self.object_type}-{self.lineage_id}"


class NextObjectVersion(BaseModel):
    UUID: uuid.UUID
    Title: str
    Start_Validity: datetime
    End_Validity: Optional[datetime] = None
    Created_Date: datetime
    Modified_Date: datetime
    Previous_UUID: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
