import uuid
from datetime import datetime

from sqlalchemy import LargeBinary, Unicode
from sqlalchemy.orm import Mapped, deferred, mapped_column

from app.core.db.base import Base


class SourceWerkingsgebiedenTable(Base):
    __tablename__ = "Werkingsgebieden"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    ID: Mapped[int]
    Created_Date: Mapped[datetime]
    Modified_Date: Mapped[datetime]

    Start_Validity: Mapped[datetime] = mapped_column(name="Begin_Geldigheid")
    End_Validity: Mapped[datetime] = mapped_column(name="Eind_Geldigheid")

    Title: Mapped[str] = mapped_column(name="Werkingsgebied")
    SHAPE: Mapped[bytes] = deferred(mapped_column(LargeBinary()))
    GML: Mapped[str] = deferred(mapped_column(Unicode))
    symbol: Mapped[str] = mapped_column(Unicode(265))

    def __repr__(self) -> str:
        return f"SourceWerkingsgebiedenTable(UUID={self.UUID!r}, Title={self.Title!r})"
