from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.dynamic.db.objects_table import ObjectsTable


class StaticBaseColumns:
    Object_Type: Mapped[str] = mapped_column(String(25))
    Object_ID: Mapped[int]
    Code: Mapped[str] = mapped_column(String(35), primary_key=True)


class ObjectStaticsTable(Base, StaticBaseColumns):
    __tablename__ = "object_statics"

    Objects: Mapped[List[ObjectsTable]] = relationship(
        "ObjectsTable", back_populates="ObjectStatics", lazy="select"
    )

    def __repr__(self) -> str:
        return f"ObjectStatics(Code={self.Code!r})"
