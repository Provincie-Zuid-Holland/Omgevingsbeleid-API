from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ObjectStaticsTable(Base):
    __tablename__ = "object_statics"

    Object_Type: Mapped[str] = mapped_column(String(25))
    Object_ID: Mapped[int]
    Code: Mapped[str] = mapped_column(String(35), primary_key=True)

    def __repr__(self) -> str:
        return f"ObjectStatics(Code={self.Code!r}"
