from datetime import datetime
import uuid

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base


class WerkingsgebiedenTable(Base):
    __tablename__ = "Werkingsgebieden"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    ID: Mapped[int]
    Created_Date: Mapped[datetime]
    Modified_Date: Mapped[datetime]

    Title: Mapped[str] = mapped_column(name="Werkingsgebied")

    def __repr__(self) -> str:
        return f"Werkingsgebieden(UUID={self.UUID!r}, ID={self.ID!r})"
