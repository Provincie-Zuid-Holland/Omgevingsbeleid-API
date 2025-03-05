from abc import ABCMeta
from typing import Any, Dict, List, Type

from pydantic import BaseModel


class Column(BaseModel):
    id: str
    name: str
    type: str
    type_data: dict = {}
    nullable: bool = False
    static: bool = False
    serializers: List[str] = []
    deserializers: List[str] = []


class Field(BaseModel):
    id: str
    column: str
    name: str
    type: str
    optional: bool
    validators: List[dict] = []
    formatters: List[dict] = []
    default: Any = None

    def overwrite(self, overwrites: dict):
        if not overwrites:
            return
        if "optional" in overwrites:
            self.optional = overwrites["optional"]
        if "validators" in overwrites:
            self.validators = overwrites["validators"]
        if "formatters" in overwrites:
            self.formatters = overwrites["formatters"]
        if "default" in overwrites:
            self.default = overwrites["default"]


class IntermediateModel(BaseModel):
    id: str
    name: str
    static_only: bool

    # Determines the columns to fetch from the database
    columns: List[str]

    # Used to generate the pydantic model
    fields: List[Field]

    # Fields from the static table
    static_fields: List[Field]

    # Services can add data to fields and columns
    service_config: dict

    model_validators: dict


class EndpointConfig(BaseModel):
    prefix: str
    resolver_id: str
    resolver_data: dict


class Api(BaseModel):
    id: str
    object_type: str
    endpoint_configs: List[EndpointConfig]


class IntermediateObject(BaseModel):
    id: str
    columns: Dict[str, Column]
    fields: Dict[str, Field]
    config: dict
    api: Api


class Model(BaseModel, metaclass=ABCMeta):
    id: str
    name: str
    pydantic_model: Type[BaseModel]


class DynamicObjectModel(Model):
    service_config: dict
    columns: List[Column]


class ExtensionModel(Model):
    pass
