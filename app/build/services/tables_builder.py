from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Unicode, Uuid
from sqlalchemy.orm import mapped_column

from app.build.events.event_manager import BuildEventManager
from app.build.events.generate_table_event import GenerateTableEvent
from app.core.db.base import Base
from app.core.tables.modules import ModuleObjectsTable
from app.core.tables.objects import ObjectsTable, ObjectStaticsTable
from app.core.types import Column


class TablesBuilder:
    COLUMN_TYPE_MAP: dict[str, Any] = {
        "int": Integer,
        "str": Unicode,
        "str_25": Unicode(25),
        "str_35": Unicode(35),
        "datetime": DateTime,
        "object_uuid": Uuid,
        "json": JSON,
        "uuid": Uuid,
    }

    def __init__(self, event_manager: BuildEventManager):
        self._event_manager: BuildEventManager = event_manager

    def build_tables(self, columns: dict[str, Column]):
        self._generate_table(ObjectStaticsTable, "ObjectStaticsTable", columns, static=True)
        ObjectStaticsTable.Cached_Title = mapped_column("Cached_Title", String(255), nullable=True)

        self._generate_table(ObjectsTable, "ObjectsTable", columns, static=False)
        self._generate_table(ModuleObjectsTable, "ModuleObjectsTable", columns, static=False)

    def _generate_table(
        self,
        table_type: type[Base],
        table_name: str,
        columns: dict[str, Column],
        static: bool,
    ):
        for column in columns.values():
            if column.static != static:
                continue

            if hasattr(table_type, column.name):
                continue

            if column.type in self.COLUMN_TYPE_MAP:
                self._handle_base_type(table_type, column, self.COLUMN_TYPE_MAP[column.type])
                continue

            self._event_manager.dispatch(GenerateTableEvent(table_type, table_name, column))

    def _handle_base_type(self, table_type: type[Base], column: Column, column_type: Any):
        setattr(
            table_type,
            column.name,
            mapped_column(
                column.name,
                column_type,
                nullable=column.nullable,
            ),
        )
