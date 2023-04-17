from typing import Dict
from copy import deepcopy

from ..models import Column


def columns_loader(base_columns: Dict[str, Column], config: dict) -> Dict[str, Column]:
    columns: Dict[str, Column] = deepcopy(base_columns)

    for column_id, data in config.items():
        if column_id in columns:
            raise RuntimeError(f"Column ID: '{column_id}' already exists")

        columns[column_id] = Column(
            id=column_id,
            name=data.get("name"),
            type=data.get("type"),
            type_data=data.get("type_data", {}),
            nullable=data.get("nullable", False),
            static=data.get("static", False),
            serializers=data.get("serializers", []),
            deserializers=data.get("deserializers", []),
        )

    return columns
