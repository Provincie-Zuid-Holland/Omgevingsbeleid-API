from typing import List

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
