from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from sqlalchemy.orm import Mapped, declarative_base, relationship

from app.core.db.mixins import HasIDType, TimeStamped
from app.dynamic.db.object_static_table import StaticBaseColumns
from app.dynamic.db.objects_table import ObjectBaseColumns
from app.dynamic.dynamic_app import DynamicApp
from app.extensions.users.db.tables import UserBaseColumns


class LocalTables(BaseModel):
    Base: type
    ObjectsTable: type
    ObjectStaticsTable: type
    UsersTabel: type

    class Config:
        arbitrary_types_allowed = True


class LocalTableFactory:
    # Important to generate new declarative base,
    # or table state will persist in the test session.
    # TODO: find more scalable way to setup DeclarativeBase+Table

    def __init__(self):
        self.base = declarative_base()
        self.statics_table = self._generate_statics_table()
        self.objects_table = self._generate_objects_table()
        self.users_table = self._generate_users_table()

        self.local_tables = self._build_table()

    def _build_table(self) -> LocalTables:
        return LocalTables(
            Base=self.base,
            ObjectsTable=self.objects_table,
            ObjectStaticsTable=self.statics_table,
            UsersTabel=self.users_table,
        )

    def _generate_statics_table(self):
        class LocalObjectStaticsTable(self.base, StaticBaseColumns):
            __tablename__ = "object_statics"
            Test_Field: Mapped[Optional[str]]

        return LocalObjectStaticsTable

    def _generate_objects_table(self):
        class LocalObjectsTable(self.base, ObjectBaseColumns, TimeStamped, HasIDType):
            __tablename__ = "objects"
            Start_Validity: Mapped[datetime]
            End_Validity: Mapped[Optional[datetime]]

            ObjectStatics: Mapped["LocalObjectStaticsTable"] = relationship()

        return LocalObjectsTable

    def _generate_users_table(self):
        class LocalUsersTable(self.base, UserBaseColumns):
            __tablename__ = "Gebruikers"

        return LocalUsersTable


class FakeExtension:
    def __init__(self):
        self.calls = []

    def initialize(self, config):
        self.calls.append(("initialize", config))

    def register_listeners(self, *args):
        self.calls.append(("register_listeners", args))

    def register_commands(self, *args):
        self.calls.append(("register_commands", args))

    def register_base_columns(self):
        self.calls.append(("register_base_columns",))
        return []

    def register_base_fields(self):
        self.calls.append(("register_base_fields",))
        return []

    def register_endpoint_resolvers(self, *args):
        self.calls.append(("register_endpoint_resolvers", args))
        return []

    def register_tables(self, *args):
        self.calls.append(("register_tables", args))

    def register_models(self, *args):
        self.calls.append(("register_models", args))

    def register_endpoints(self, *args):
        self.calls.append(("register_endpoints", args))


class MockResponseModel(BaseModel):
    Object_ID: Optional[str]
    UUID: UUID
    Object_Type: str
    Modified_Date: Optional[datetime]
    Start_Validity: datetime
    End_Validity: Optional[datetime]


class TestDynamicApp(BaseModel):
    dynamic_app: DynamicApp
    local_tables: LocalTables

    class Config:
        arbitrary_types_allowed = True
