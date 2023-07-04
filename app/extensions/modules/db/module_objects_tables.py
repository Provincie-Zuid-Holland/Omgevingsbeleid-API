import uuid

from sqlalchemy import ForeignKey, ForeignKeyConstraint, Unicode
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.session import object_session

from app.core.db import Base
from app.dynamic.db import ObjectsTable

from .tables import ModuleObjectContextTable


class ModuleObjectsColumns:
    Module_ID: Mapped[int] = mapped_column(ForeignKey("modules.Module_ID"))
    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Code: Mapped[str] = mapped_column(Unicode(35), ForeignKey("object_statics.Code"))
    Deleted: Mapped[bool] = mapped_column(default=False)


class ModuleObjectAttributes(ModuleObjectsColumns):
    """
    All ORM column fields including dynamic / hybrid properties
    """

    @hybrid_property
    def has_valid_version(self) -> bool:
        # True if a matching code exists in Objects table
        session = object_session(self)
        return session.query(ObjectsTable).filter(ObjectsTable.Code == self.Code).exists()


class ModuleObjectsTable(Base, ModuleObjectAttributes):
    __tablename__ = "module_objects"

    ModuleObjectContext: Mapped["ModuleObjectContextTable"] = relationship()
    ObjectStatics: Mapped["ObjectStaticsTable"] = relationship(viewonly=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["Module_ID", "Code"],
            ["module_object_context.Module_ID", "module_object_context.Code"],
        ),
    )
