from typing import Any, Dict
import uuid

from sqlalchemy import ForeignKey, Integer, String, DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.dynamic.config.models import Column as DynamicColumn


class ObjectsTable(Base):
    __tablename__ = "objects"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Code: Mapped[str] = mapped_column(String(35), ForeignKey("object_statics.Code"))


# @todo: this should be filled by extension registers and provided by dynamic_app
column_type_map: Dict[str, Any] = {
    "int": Integer,
    "str": String,
    "str_25": String(25),
    "str_35": String(35),
    "datetime": DateTime,
    "object_uuid": Uuid,
    "user_uuid": Uuid,
    "werkingsgebied_uuid": Uuid,
}


# @todo: this should be filled by extension registers and provided by dynamic_app
foreign_key_map: Dict[str, str] = {
    "user_uuid": "Gebruikers.UUID",
    "werkingsgebied_uuid": "Werkingsgebieden.UUID",
}


def generate_dynamic_objects(columns: Dict[str, DynamicColumn]):
    for _, column in columns.items():
        if column.id in ["uuid", "code"]:
            continue

        if column.static:
            continue

        if not column.type in column_type_map:
            raise RuntimeError(f"Invalid column type '{column.type}'")
        column_type = column_type_map[column.type]

        additional_args = []
        if column.type in foreign_key_map:
            additional_args.append(ForeignKey(foreign_key_map[column.type]))

        setattr(
            ObjectsTable,
            column.name,
            mapped_column(
                column.name, column_type, nullable=column.nullable, *additional_args
            ),
        )
