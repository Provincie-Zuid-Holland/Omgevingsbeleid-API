from typing import Any

from pydantic import BaseModel
from pydantic import Field as PydanticField

from app.core.types import Column


class FieldType(BaseModel):
    id: str
    field_type: Any
    default: Any

    def __hash__(self):
        return hash(self.id)


class Field(BaseModel):
    id: str
    column: str
    name: str
    type: str
    optional: bool
    validators: list[dict] = PydanticField(default_factory=list)
    formatters: list[dict] = PydanticField(default_factory=list)
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
    columns: list[Column]  # Determines the columns to fetch from the database
    fields: list[Field]  # Used to generate the pydantic model
    static_fields: list[Field]  # Fields from the static table
    service_config: dict  # Services can add data to fields and columns
    model_validators: dict
    dependency_model_ids: list[str] = PydanticField(default_factory=list)


class EndpointConfig(BaseModel):
    prefix: str
    resolver_id: str
    resolver_data: dict


class ObjectApi(BaseModel):
    object_id: str
    object_type: str
    endpoint_configs: list[EndpointConfig]


class IntermediateObject(BaseModel):
    id: str
    object_type: str
    fields: dict[str, Field]
    config: dict
    api: ObjectApi
    intermediate_models: list[IntermediateModel]


class BuildData(BaseModel):
    main_config: dict
    object_configs: list[dict]
    columns: dict[str, Column]
    object_intermediates: list[IntermediateObject]
