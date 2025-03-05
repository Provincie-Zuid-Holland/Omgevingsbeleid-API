from pydantic import BaseModel, Field, field_validator


class WriteRelation(BaseModel):
    Object_ID: int
    Object_Type: str
    Description: str = Field("", nullable=True)

    @field_validator("Description", mode="before")
    @classmethod
    def default_empty_string(cls, v):
        return v or ""

    @property
    def Code(self) -> str:
        return f"{self.Object_Type}-{self.Object_ID}"


class ReadRelationShort(BaseModel):
    Object_ID: int
    Object_Type: str
    Description: str = Field("", nullable=True)

    @field_validator("Description", mode="before")
    @classmethod
    def default_empty_string(cls, v):
        return v or ""

    @property
    def Code(self) -> str:
        return f"{self.Object_Type}-{self.Object_ID}"


class ReadRelation(BaseModel):
    Object_ID: int
    Object_Type: str
    Description: str = Field("", nullable=True)
    Title: str = Field("", nullable=True)

    @field_validator("Description", "Title", mode="before")
    @classmethod
    def default_empty_string(cls, v):
        return v or ""

    @property
    def Code(self) -> str:
        return f"{self.Object_Type}-{self.Object_ID}"
