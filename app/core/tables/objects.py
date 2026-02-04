import uuid
from typing import List, Optional

from sqlalchemy import ForeignKey, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base
from app.core.db.mixins import SerializerMixin


class ObjectsTable(Base, SerializerMixin):
    __tablename__ = "objects"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=lambda: uuid.uuid4())
    Code: Mapped[str] = mapped_column(Unicode(35), ForeignKey("object_statics.Code"))

    ObjectStatics: Mapped["ObjectStaticsTable"] = relationship(
        "ObjectStaticsTable",
        primaryjoin="ObjectsTable.Code == ObjectStaticsTable.Code",
        back_populates="Objects",
        lazy="select",
    )


class ObjectStaticsTable(Base, SerializerMixin):
    __tablename__ = "object_statics"

    Object_Type: Mapped[str] = mapped_column(Unicode(25))
    Object_ID: Mapped[int]
    Code: Mapped[str] = mapped_column(Unicode(35), primary_key=True)
    Source_Identifier: Mapped[Optional[str]] = mapped_column(Unicode(255), nullable=True)

    Objects: Mapped[List[ObjectsTable]] = relationship(
        "ObjectsTable",
        primaryjoin="ObjectStaticsTable.Code == ObjectsTable.Code",
        back_populates="ObjectStatics",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"ObjectStatics(Code={self.Code!r})"
