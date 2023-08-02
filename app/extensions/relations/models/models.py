from pydantic import BaseModel, Field, validator


class WriteRelation(BaseModel):
    Object_ID: int
    Object_Type: str
    Description: str = Field("", nullable=True)

    @validator("Description", pre=True)
    def default_empty_string(cls, v):
        return v or ""

    @property
    def Code(self) -> str:
        return f"{self.Object_Type}-{self.Object_ID}"


class ReadRelationShort(BaseModel):
    Object_ID: int
    Object_Type: str
    Description: str = Field("", nullable=True)

    @validator("Description", pre=True)
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

    @validator("Description", "Title", pre=True)
    def default_empty_string(cls, v):
        return v or ""

    @property
    def Code(self) -> str:
        return f"{self.Object_Type}-{self.Object_ID}"
