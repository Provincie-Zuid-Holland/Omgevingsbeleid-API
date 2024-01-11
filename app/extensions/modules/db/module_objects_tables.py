import uuid

from sqlalchemy import ForeignKey, ForeignKeyConstraint, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

from .tables import ModuleObjectContextTable


class ModuleObjectsColumns:
    Module_ID: Mapped[int] = mapped_column(ForeignKey("modules.Module_ID"))
    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Code: Mapped[str] = mapped_column(Unicode(35), ForeignKey("object_statics.Code"))
    Deleted: Mapped[bool] = mapped_column(default=False)


class ModuleObjectsTable(Base, ModuleObjectsColumns):
    __tablename__ = "module_objects"

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
