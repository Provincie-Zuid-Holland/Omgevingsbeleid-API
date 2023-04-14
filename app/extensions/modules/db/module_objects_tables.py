import uuid

from sqlalchemy import ForeignKey, ForeignKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.dynamic.db.object_static_table import ObjectStaticsTable
from .tables import ModuleObjectContextTable


class ModuleObjectsColumns:
    Module_ID: Mapped[int] = mapped_column(ForeignKey("modules.Module_ID"))
    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Code: Mapped[str] = mapped_column(String(35), ForeignKey("object_statics.Code"))
    Deleted: Mapped[bool] = mapped_column(default=False)


class ModuleObjectsTable(Base, ModuleObjectsColumns):
    __tablename__ = "module_objects"

    ModuleObjectContext: Mapped["ModuleObjectContextTable"] = relationship()
    ObjectStatics: Mapped["ObjectStaticsTable"] = relationship(viewonly=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["Module_ID", "Code"],
            ["module_object_context.Module_ID", "module_object_context.Code"],
        ),
    )
