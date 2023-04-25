import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy import ForeignKey, String

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base
from app.core.db.mixins import TimeStamped, UserMetaData


class ModuleBaseColumns(TimeStamped, UserMetaData):
    Module_ID: Mapped[int] = mapped_column(primary_key=True)

    Activated: Mapped[bool] = mapped_column(default=False)
    Closed: Mapped[bool] = mapped_column(default=False)
    Successful: Mapped[bool] = mapped_column(default=False)
    Temporary_Locked: Mapped[bool] = mapped_column(default=False)

    Title: Mapped[str] = mapped_column(default="")
    Description: Mapped[str] = mapped_column(default="")
    Module_Manager_1_UUID: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("Gebruikers.UUID")
    )
    Module_Manager_2_UUID: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("Gebruikers.UUID")
    )

    Start_Validity: Mapped[Optional[datetime]]
    End_Validity: Mapped[Optional[datetime]]

    @property
    def Status(self) -> Optional["ModuleStatusHistoryTable"]:
        if not self.status_history:
            return None
        return self.status_history[-1]

    def is_manager(self, user_uuid: uuid.UUID) -> bool:
        return user_uuid in [self.Module_Manager_1_UUID, self.Module_Manager_2_UUID]


class ModuleTable(Base, ModuleBaseColumns):
    __tablename__ = "modules"

    status_history: Mapped[List["ModuleStatusHistoryTable"]] = relationship(
        back_populates="Module", order_by="asc(ModuleStatusHistoryTable.Created_Date)"
    )

    Created_By: Mapped[List["UsersTable"]] = relationship(
        primaryjoin="ModuleTable.Created_By_UUID == UsersTable.UUID"
    )
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
        return f"Module(Module_ID={self.Module_ID!r}, Title={self.Title!r}"


class ModuleStatusHistoryColumns:
    ID: Mapped[int] = mapped_column(primary_key=True)
    Module_ID: Mapped[int] = mapped_column(ForeignKey("modules.Module_ID"))

    Created_Date: Mapped[datetime]
    Created_By_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))

    Status: Mapped[str]


class ModuleStatusHistoryTable(Base, ModuleStatusHistoryColumns):
    __tablename__ = "module_status_history"

    Module: Mapped[ModuleTable] = relationship(back_populates="status_history")

    def __repr__(self) -> str:
        return f"ModuleStatusHistory(ID={self.ID!r}), Module_ID={self.Module_ID!r}"


class ModuleObjectContextColumns:
    Module_ID = mapped_column(ForeignKey("modules.Module_ID"), primary_key=True)

    Object_Type: Mapped[str] = mapped_column(String(25))
    Object_ID: Mapped[int]
    Code: Mapped[str] = mapped_column(String(35), primary_key=True)

    Original_Adjust_On: Mapped[Optional[uuid.UUID]]

    Hidden: Mapped[bool] = mapped_column(default=False)
    Action: Mapped[str]
    Explanation: Mapped[str]
    Conclusion: Mapped[str]


class ModuleObjectContextTable(
    Base, ModuleObjectContextColumns, TimeStamped, UserMetaData
):
    __tablename__ = "module_object_context"

    Created_By: Mapped[List["UsersTable"]] = relationship(
        primaryjoin="ModuleObjectContextTable.Created_By_UUID == UsersTable.UUID"
    )
    Modified_By: Mapped[List["UsersTable"]] = relationship(
        primaryjoin="ModuleObjectContextTable.Modified_By_UUID == UsersTable.UUID"
    )
