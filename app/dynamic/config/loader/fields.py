from copy import deepcopy
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from ..models import Field

field_types = {
    "int": int,
    "float": float,
    "str": str,
    "uuid": UUID,
    "datetime": datetime,
    "list_str": Optional[List[str]],
}


field_defaults = {
    "none": None,
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
