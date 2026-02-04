from typing import Any, Dict, Type

from sqlalchemy import JSON, DateTime, Integer, String, Unicode, Uuid
from sqlalchemy.orm import mapped_column

from app.build.events.generate_table_event import GenerateTableEvent
from app.core.db.base import Base
from app.core.services.event.event_manager import EventManager
from app.core.tables.modules import ModuleObjectsTable
from app.core.tables.objects import ObjectStaticsTable, ObjectsTable
from app.core.types import Column
from sqlalchemy.orm import Session


class TablesBuilder:
    COLUMN_TYPE_MAP: Dict[str, Any] = {
        "int": Integer,
        "str": Unicode,
        "str_25": Unicode(25),
        "str_35": Unicode(35),
        "datetime": DateTime,
        "object_uuid": Uuid,
        "json": JSON,
        "uuid": Uuid,
    }

    def __init__(self, event_manager: EventManager):
        self._event_manager: EventManager = event_manager

    def build_tables(self, session: Session, columns: Dict[str, Column]):
        self._generate_table(session, ObjectStaticsTable, "ObjectStaticsTable", columns, static=True)
        setattr(ObjectStaticsTable, "Cached_Title", mapped_column("Cached_Title", String(255), nullable=True))

        self._generate_table(session, ObjectsTable, "ObjectsTable", columns, static=False)
        self._generate_table(session, ModuleObjectsTable, "ModuleObjectsTable", columns, static=False)

    def _generate_table(
        self,
        session: Session,
        table_type: Type[Base],
        table_name: str,
        columns: Dict[str, Column],
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

            self._event_manager.dispatch(session, GenerateTableEvent(table_type, table_name, column))

    def _handle_base_type(self, table_type: Type[Base], column: Column, column_type: Any):
        setattr(
            table_type,
            column.name,
            mapped_column(
                column.name,
                column_type,
                nullable=column.nullable,
            ),
        )
