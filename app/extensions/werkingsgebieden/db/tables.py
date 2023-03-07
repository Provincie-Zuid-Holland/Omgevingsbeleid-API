from datetime import datetime
import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base


class WerkingsgebiedenTable(Base):
    __tablename__ = "Werkingsgebieden"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    ID: Mapped[int]
    Created_Date: Mapped[datetime]
    Modified_Date: Mapped[datetime]
    Werkingsgebied: Mapped[str]

    def __repr__(self) -> str:
        return f"Werkingsgebieden(UUID={self.UUID!r}, ID={self.ID!r})"


class ObjectWerkingsgebiedenTable(Base):
    __tablename__ = "object_werkingsgebieden"

    Object_Code: Mapped[str] = mapped_column(
        ForeignKey("object_statics.Code"), primary_key=True
    )
    Werkingsgebied_UUID: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("Werkingsgebieden.UUID"), primary_key=True
    )
    Description: Mapped[str]

    def __repr__(self) -> str:
        return f"ObjectWerkingsgebieden(Object_Code={self.Object_Code!r}, Werkingsgebied_UUID={self.Werkingsgebied_UUID!r})"
