from pydantic import BaseModel, Field, field_validator


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
