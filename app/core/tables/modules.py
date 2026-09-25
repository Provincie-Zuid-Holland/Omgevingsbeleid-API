import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, ForeignKeyConstraint, Unicode
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import or_, select

from app.core.db.base import Base
from app.core.db.mixins import SerializerMixin, TimeStamped, UserMetaData
from app.core.tables.objects import ObjectStaticsTable
from app.core.tables.users import UsersTable


class ModuleTable(Base, TimeStamped, UserMetaData):
    __tablename__ = "modules"

    module_id: Mapped[int] = mapped_column(primary_key=True)

    activated: Mapped[bool] = mapped_column(default=False)
    closed: Mapped[bool] = mapped_column(default=False)
    successful: Mapped[bool] = mapped_column(default=False)
    temporary_locked: Mapped[bool] = mapped_column(default=False)

    title: Mapped[str] = mapped_column(default="")
    description: Mapped[str] = mapped_column(default="")
    module_manager_1_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("Gebruikers.UUID"))
    module_manager_2_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("Gebruikers.UUID"))

    @property
    def status(self) -> Optional["ModuleStatusHistoryTable"]:
        return None if not self.status_history else self.status_history[-1]

    @hybrid_property
    def current_status(self) -> str | None:
        if not self.status_history:
            return None
        return self.status_history[-1].status

    @current_status.expression
    def current_status(cls):
        return (
            select(ModuleStatusHistoryTable.status)
            .filter(cls.module_id == ModuleStatusHistoryTable.module_id)
            .order_by(ModuleStatusHistoryTable.id.desc())
            .limit(1)
            .scalar_subquery()
        )

    @hybrid_method
    def is_manager(self, user_id):
        return user_id in [self.module_manager_1_id, self.module_manager_2_id]

    @is_manager.expression
    def is_manager(cls, user_id):
        return or_(
            cls.module_manager_1_id == user_id,
            cls.module_manager_2_id == user_id,
        )

    @hybrid_property
    def is_active(self) -> bool:
        return not self.closed and self.activated

    @is_active.expression
    def is_active(cls):
        return (cls.activated == True) & (cls.closed == False)  # type: ignore

    status_history: Mapped[list["ModuleStatusHistoryTable"]] = relationship(
        back_populates="module", order_by="asc(ModuleStatusHistoryTable.id)"
    )

    created_by: Mapped[list["UsersTable"]] = relationship(primaryjoin="ModuleTable.created_by_id == UsersTable.UUID")
    modified_by: Mapped[list["UsersTable"]] = relationship(primaryjoin="ModuleTable.modified_by_id == UsersTable.UUID")
    module_manager_1: Mapped[list["UsersTable"]] = relationship(
        primaryjoin="ModuleTable.module_manager_1_id == UsersTable.UUID"
    )
    module_manager_2: Mapped[list["UsersTable"]] = relationship(
        primaryjoin="ModuleTable.module_manager_2_id == UsersTable.UUID"
    )

    def __repr__(self) -> str:
        return f"Module(module_id={self.module_id!r}, title={self.title!r})"


class ModuleStatusHistoryTable(Base):
    __tablename__ = "module_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.module_id"))

    created_date: Mapped[datetime]
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))

    status: Mapped[str]

    module: Mapped[ModuleTable] = relationship(back_populates="status_history")

    def __repr__(self) -> str:
        return f"ModuleStatusHistory(id={self.id!r}, module_id={self.module_id!r}, status={self.status!r})"


class ModuleObjectsTable(Base):
    __tablename__ = "module_objects"

    module_id: Mapped[int] = mapped_column(ForeignKey("modules.module_id"))
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(Unicode(35), ForeignKey("object_statics.code"))
    deleted: Mapped[bool] = mapped_column(default=False)

    module_object_context: Mapped["ModuleObjectContextTable"] = relationship()
    object_statics: Mapped[ObjectStaticsTable] = relationship(
        primaryjoin="ModuleObjectsTable.code == ObjectStaticsTable.code",
        viewonly=True,
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["module_id", "code"],
            ["module_object_context.module_id", "module_object_context.code"],
        ),
    )

    def __repr__(self) -> str:
        return f"ModuleObjectsTable(module_id={self.module_id!r}, uuid={self.id!r}, code={self.code!r})"


class ModuleObjectContextTable(Base, TimeStamped, UserMetaData, SerializerMixin):
    __tablename__ = "module_object_context"

    module_id = mapped_column(ForeignKey("modules.module_id"), primary_key=True)

    object_type: Mapped[str] = mapped_column(Unicode(25))
    object_id: Mapped[int]
    code: Mapped[str] = mapped_column(Unicode(35), primary_key=True)

    original_adjust_on: Mapped[uuid.UUID | None]

    hidden: Mapped[bool] = mapped_column(default=False)
    action: Mapped[str]
    explanation: Mapped[str]
    conclusion: Mapped[str]

    created_by: Mapped[list["UsersTable"]] = relationship(
        primaryjoin="ModuleObjectContextTable.created_by_id == UsersTable.UUID"
    )
    modified_by: Mapped[list["UsersTable"]] = relationship(
        primaryjoin="ModuleObjectContextTable.modified_by_id == UsersTable.UUID"
    )

    def __repr__(self) -> str:
        return f"ModuleObjectContextTable(module_id={self.module_id!r}, code={self.code!r}, action={self.action!r})"
