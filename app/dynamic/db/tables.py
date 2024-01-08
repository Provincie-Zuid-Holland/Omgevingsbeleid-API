import uuid
from typing import List

from sqlalchemy import ForeignKey, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.db.mixins import SerializerMixin


class ObjectBaseColumns:
    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=lambda: uuid.uuid4())
    Code: Mapped[str] = mapped_column(Unicode(35), ForeignKey("object_statics.Code"))


class ObjectsTable(Base, ObjectBaseColumns, SerializerMixin):
    __tablename__ = "objects"

    ObjectStatics: Mapped["ObjectStaticsTable"] = relationship(
        "ObjectStaticsTable",
        primaryjoin="ObjectsTable.Code == ObjectStaticsTable.Code",
        back_populates="Objects",
        lazy="select",
    )


class StaticBaseColumns:
    Object_Type: Mapped[str] = mapped_column(Unicode(25))
    Object_ID: Mapped[int]
    Code: Mapped[str] = mapped_column(Unicode(35), primary_key=True)


class ObjectStaticsTable(Base, StaticBaseColumns, SerializerMixin):
    __tablename__ = "object_statics"

    Objects: Mapped[List[ObjectsTable]] = relationship(
        "ObjectsTable",
        primaryjoin="ObjectStaticsTable.Code == ObjectsTable.Code",
        back_populates="ObjectStatics",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"ObjectStatics(Code={self.Code!r})"
