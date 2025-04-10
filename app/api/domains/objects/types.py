from typing import List

from pydantic import BaseModel, ConfigDict, RootModel


class ObjectCount(BaseModel):
    object_type: str
    count: int

    model_config = ConfigDict(from_attributes=True)


# Wraps a List type to a Pyndantic model type for FastAPI
ObjectCountResponse = RootModel[List[ObjectCount]]
