import uuid
from datetime import datetime

from sqlalchemy import BLOB, Unicode
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base


class WerkingsgebiedenTable(Base):
    __tablename__ = "Werkingsgebieden"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    ID: Mapped[int]
    Created_Date: Mapped[datetime]
    Modified_Date: Mapped[datetime]

    Start_Validity: Mapped[datetime] = mapped_column(name="Begin_Geldigheid")
    End_Validity: Mapped[datetime] = mapped_column(name="Eind_Geldigheid")

    Title: Mapped[str] = mapped_column(name="Werkingsgebied")
    SHAPE: Mapped[bytes] = mapped_column(BLOB)
    symbol: Mapped[str] = mapped_column(Unicode(265))

    def __repr__(self) -> str:
        return f"Werkingsgebieden(UUID={self.UUID!r}, Title={self.Title!r})"


class OnderverdelingTable(Base):
    __tablename__ = "Onderverdeling"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    ID: Mapped[int]

    Title: Mapped[str] = mapped_column(name="Onderverdeling")
    SHAPE: Mapped[bytes] = mapped_column(BLOB)
    symbol: Mapped[str]
    Werkingsgebied: Mapped[str] = mapped_column(Unicode(265))
    UUID_Werkingsgebied: Mapped[uuid.UUID]

    Created_Date: Mapped[datetime]
    Modified_Date: Mapped[datetime]

    Start_Validity: Mapped[datetime] = mapped_column(name="Begin_Geldigheid")
    End_Validity: Mapped[datetime] = mapped_column(name="Eind_Geldigheid")

    def __repr__(self) -> str:
        return f"Onderverdeling(UUID={self.UUID!r}, Title={self.Title!r})"
