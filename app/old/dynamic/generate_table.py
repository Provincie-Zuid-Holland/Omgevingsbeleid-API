from typing import Any, Dict, Type

from sqlalchemy import JSON, DateTime, Integer, Unicode, Uuid
from sqlalchemy.orm import mapped_column

from app.core_old.db import Base
from app.dynamic.config.models import Column
from app.dynamic.event.generate_table_event import GenerateTableEvent
from app.dynamic.event_dispatcher import EventDispatcher

column_type_map: Dict[str, Any] = {
    "int": Integer,
    "str": Unicode,
    "str_25": Unicode(25),
    "str_35": Unicode(35),
    "datetime": DateTime,
    "object_uuid": Uuid,
    "json": JSON,
}


def generate_table(
    event_dispatcher: EventDispatcher,
    table_type: Type[Base],
    table_name: str,
    columns: Dict[str, Column],
    static: bool,
):
    for _, column in columns.items():
        if column.static != static:
            continue

        if hasattr(table_type, column.name):
            continue

        if column.type in column_type_map:
            handle_base_type(table_type, column, column_type_map[column.type])
            continue

        event_dispatcher.dispatch(GenerateTableEvent(table_type, table_name, column))


def handle_base_type(table_type: Type[Base], column: Column, column_type: Any):
    setattr(
        table_type,
        column.name,
        mapped_column(
            column.name,
            column_type,
            nullable=column.nullable,
        ),
    )
