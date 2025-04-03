import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import ForeignKey, ForeignKeyConstraint, Unicode
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import or_, select

from app.core.db.base import Base
from app.core.db.mixins import SerializerMixin, TimeStamped, UserMetaData
from app.core.tables.users import UsersTable


class ModuleTable(Base, TimeStamped, UserMetaData):
    __tablename__ = "modules"

    Module_ID: Mapped[int] = mapped_column(primary_key=True)

    Activated: Mapped[bool] = mapped_column(default=False)
    Closed: Mapped[bool] = mapped_column(default=False)
    Successful: Mapped[bool] = mapped_column(default=False)
    Temporary_Locked: Mapped[bool] = mapped_column(default=False)

    Title: Mapped[str] = mapped_column(default="")
    Description: Mapped[str] = mapped_column(default="")
    Module_Manager_1_UUID: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("Gebruikers.UUID"))
    Module_Manager_2_UUID: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("Gebruikers.UUID"))

    @property
    def Status(self) -> Optional["ModuleStatusHistoryTable"]:
        return None if not self.status_history else self.status_history[-1]

    @hybrid_property
    def Current_Status(self) -> Optional[str]:
        if not self.status_history:
            return None
        return self.status_history[-1].Status

    @Current_Status.expression
    def Current_Status(cls):
        return (
            select(ModuleStatusHistoryTable.Status)
            .filter(cls.Module_ID == ModuleStatusHistoryTable.Module_ID)
            .order_by(ModuleStatusHistoryTable.ID.desc())
            .limit(1)
            .scalar_subquery()
        )

    @hybrid_method
    def is_manager(self, user_uuid):
        return user_uuid in [self.Module_Manager_1_UUID, self.Module_Manager_2_UUID]

    @is_manager.expression
    def is_manager(cls, user_uuid):
        return or_(
            cls.Module_Manager_1_UUID == user_uuid,
            cls.Module_Manager_2_UUID == user_uuid,
        )

    @hybrid_property
    def is_active(self) -> bool:
        return not self.Closed and self.Activated

    @is_active.expression
    def is_active(cls):
        return (not cls.Closed) & cls.Activated

    status_history: Mapped[List["ModuleStatusHistoryTable"]] = relationship(
        back_populates="Module", order_by="asc(ModuleStatusHistoryTable.ID)"
    )

    Created_By: Mapped[List["UsersTable"]] = relationship(primaryjoin="ModuleTable.Created_By_UUID == UsersTable.UUID")
    Modified_By: Mapped[List["UsersTable"]] = relationship(
        primaryjoin="ModuleTable.Modified_By_UUID == UsersTable.UUID"
    )
    Module_Manager_1: Mapped[List["UsersTable"]] = relationship(
        primaryjoin="ModuleTable.Module_Manager_1_UUID == UsersTable.UUID"
    )
    Module_Manager_2: Mapped[List["UsersTable"]] = relationship(
        primaryjoin="ModuleTable.Module_Manager_2_UUID == UsersTable.UUID"
    )

    def __repr__(self) -> str:
        return f"Module(Module_ID={self.Module_ID!r}, Title={self.Title!r})"


class ModuleStatusHistoryTable(Base):
    __tablename__ = "module_status_history"

    ID: Mapped[int] = mapped_column(primary_key=True)
    Module_ID: Mapped[int] = mapped_column(ForeignKey("modules.Module_ID"))

    Created_Date: Mapped[datetime]
    Created_By_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))

    Status: Mapped[str]

    Module: Mapped[ModuleTable] = relationship(back_populates="status_history")

    def __repr__(self) -> str:
        return f"ModuleStatusHistory(ID={self.ID!r}), Module_ID={self.Module_ID!r}"


class ModuleObjectsTable(Base):
    __tablename__ = "module_objects"

    Module_ID: Mapped[int] = mapped_column(ForeignKey("modules.Module_ID"))
    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Code: Mapped[str] = mapped_column(Unicode(35), ForeignKey("object_statics.Code"))
    Deleted: Mapped[bool] = mapped_column(default=False)

    ModuleObjectContext: Mapped["ModuleObjectContextTable"] = relationship()
    ObjectStatics: Mapped["ObjectStaticsTable"] = relationship(
        primaryjoin="ModuleObjectsTable.Code == ObjectStaticsTable.Code",
        viewonly=True,
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["Module_ID", "Code"],
            ["module_object_context.Module_ID", "module_object_context.Code"],
        ),
    )

    def __repr__(self) -> str:
        return f"ModuleObjectsTable(Module_ID={self.Module_ID!r}, UUID={self.UUID!r}, Code={self.Code!r})"


class ModuleObjectContextTable(Base, TimeStamped, UserMetaData, SerializerMixin):
    __tablename__ = "module_object_context"

    Module_ID = mapped_column(ForeignKey("modules.Module_ID"), primary_key=True)

    Object_Type: Mapped[str] = mapped_column(Unicode(25))
    Object_ID: Mapped[int]
    Code: Mapped[str] = mapped_column(Unicode(35), primary_key=True)

    Original_Adjust_On: Mapped[Optional[uuid.UUID]]

    Hidden: Mapped[bool] = mapped_column(default=False)
    Action: Mapped[str]
    Explanation: Mapped[str]
    Conclusion: Mapped[str]

    Created_By: Mapped[List["UsersTable"]] = relationship(
        primaryjoin="ModuleObjectContextTable.Created_By_UUID == UsersTable.UUID"
    )
    Modified_By: Mapped[List["UsersTable"]] = relationship(
        primaryjoin="ModuleObjectContextTable.Modified_By_UUID == UsersTable.UUID"
    )
