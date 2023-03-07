from typing import Any, Dict

from sqlalchemy import ForeignKey, Integer, String, DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.dynamic.config.models import Column as DynamicColumn


class ObjectStaticsTable(Base):
    __tablename__ = "object_statics"

    Object_Type: Mapped[str] = mapped_column(String(25))
    Object_ID: Mapped[int]
    Code: Mapped[str] = mapped_column(String(35), primary_key=True)

    def __repr__(self) -> str:
        return f"ObjectStatics(Code={self.Code!r}"


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


def generate_dynamic_object_statics(columns: Dict[str, DynamicColumn]):
    for _, column in columns.items():
        if not column.static:
            continue

        if not column.type in column_type_map:
            raise RuntimeError(f"Invalid column type '{column.type}'")
        column_type = column_type_map[column.type]

        additional_args = []
        if column.type in foreign_key_map:
            additional_args.append(ForeignKey(foreign_key_map[column.type]))

        setattr(
            ObjectStaticsTable,
            column.name,
            mapped_column(
                column.name, column_type, nullable=column.nullable, *additional_args
            ),
        )
