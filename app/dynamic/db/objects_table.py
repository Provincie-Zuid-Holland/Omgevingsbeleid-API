import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.db.mixins import SerializerMixin


class ObjectBaseColumns:
    UUID: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=lambda: uuid.uuid4()
    )
    Code: Mapped[str] = mapped_column(String(35), ForeignKey("object_statics.Code"))


class ObjectsTable(Base, ObjectBaseColumns, SerializerMixin):
    __tablename__ = "objects"

    ObjectStatics: Mapped["ObjectStaticsTable"] = relationship(
        "ObjectStaticsTable", back_populates="Objects", lazy="select"
    )
