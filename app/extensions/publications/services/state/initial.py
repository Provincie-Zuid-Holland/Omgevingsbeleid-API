from pydantic import BaseModel, Field


class InitialState(BaseModel):
    Schema_Version: int = Field(1)
    Data: dict = Field({})
