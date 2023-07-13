from pydantic import BaseModel, validator


class RelationShort(BaseModel):
    Object_ID: int
    Object_Type: str
    Description: str
    Title: str

    @validator("Description", "Title", pre=True)
    def default_empty_string(cls, v):
        return v or ""

    @property
    def Code(self) -> str:
        return f"{self.Object_Type}-{self.Object_ID}"
