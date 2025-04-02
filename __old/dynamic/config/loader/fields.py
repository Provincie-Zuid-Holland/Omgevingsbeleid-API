from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from ..models import Field


@dataclass
class FieldType:
    id: str
    field_type: Any


field_types: Dict[str, FieldType] = {
    ft.id: ft
    for ft in [
        FieldType(id="int", field_type=int),
        FieldType(id="float", field_type=float),
        FieldType(id="str", field_type=str),
        FieldType(id="uuid", field_type=UUID),
        FieldType(id="datetime", field_type=datetime),
        FieldType(id="list_str", field_type=List[str]),
    ]
}


def fields_loader(base_fields: Dict[str, Field], config: dict) -> Dict[str, Field]:
    fields: Dict[str, Field] = deepcopy(base_fields)

    for field_id, data in config.items():
        if field_id in fields:
            raise RuntimeError(f"Field ID: '{field_id}' already exists")

        fields[field_id] = Field(
            id=field_id,
            column=data.get("column"),
            name=data.get("name"),
            type=data.get("type"),
            optional=data.get("optional", False),
            validators=data.get("validators", []),
            formatters=data.get("formatters", []),
        )

    return fields
