import uuid
from datetime import datetime

from sqlalchemy import BLOB
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

    def __repr__(self) -> str:
        return f"Werkingsgebieden(UUID={self.UUID!r}, Title={self.Title!r})"
