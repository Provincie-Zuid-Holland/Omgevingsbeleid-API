from pydantic import BaseModel, Field


class RelationShort(BaseModel):
    ID: int
    Object_Type: str
    Description: str = Field(default="")

    @property
    def Code(self) -> str:
        return f"{self.Object_Type}-{self.ID}"
