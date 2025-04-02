from abc import ABCMeta
from typing import List, Type

from pydantic import BaseModel, Field


class Column(BaseModel):
    id: str
    name: str
    type: str
    type_data: dict = {}
    nullable: bool = False
    static: bool = False
    serializers: List[str] = Field(default_factory=list)
    deserializers: List[str] = Field(default_factory=list)


class Model(BaseModel, metaclass=ABCMeta):
    id: str
    name: str
    pydantic_model: Type[BaseModel]


class DynamicObjectModel(Model):
    service_config: dict
    columns: List[Column]
