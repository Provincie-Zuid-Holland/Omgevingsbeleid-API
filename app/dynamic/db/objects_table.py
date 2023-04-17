import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ObjectsTable(Base):
    __tablename__ = "objects"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Code: Mapped[str] = mapped_column(String(35), ForeignKey("object_statics.Code"))

    ObjectStatics: Mapped["ObjectStaticsTable"] = relationship()
