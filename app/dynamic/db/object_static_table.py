from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class StaticBaseColumns:
    Object_Type: Mapped[str] = mapped_column(String(25))
    Object_ID: Mapped[int]
    Code: Mapped[str] = mapped_column(String(35), primary_key=True)


class ObjectStaticsTable(Base, StaticBaseColumns):
    __tablename__ = "object_statics"

    def __repr__(self) -> str:
        return f"ObjectStatics(Code={self.Code!r}"
