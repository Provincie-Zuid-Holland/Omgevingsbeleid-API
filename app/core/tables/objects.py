import uuid

from sqlalchemy import ForeignKey, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base
from app.core.db.mixins import SerializerMixin


class ObjectsTable(Base, SerializerMixin):
    __tablename__ = "objects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=lambda: uuid.uuid4())
    code: Mapped[str] = mapped_column(Unicode(35), ForeignKey("object_statics.code"))

    object_statics: Mapped["ObjectStaticsTable"] = relationship(
        "ObjectStaticsTable",
        primaryjoin="ObjectsTable.code == ObjectStaticsTable.code",
        back_populates="objects",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"ObjectsTable(id={self.id!r}, code={self.code!r})"


class ObjectStaticsTable(Base, SerializerMixin):
    __tablename__ = "object_statics"

    object_type: Mapped[str] = mapped_column(Unicode(25))
    object_id: Mapped[int]
    code: Mapped[str] = mapped_column(Unicode(35), primary_key=True)
    source_identifier: Mapped[str | None] = mapped_column(Unicode(255), nullable=True)

    objects: Mapped[list[ObjectsTable]] = relationship(
        "ObjectsTable",
        primaryjoin="ObjectStaticsTable.code == ObjectsTable.code",
        back_populates="object_statics",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"ObjectStatics(code={self.code!r})"
