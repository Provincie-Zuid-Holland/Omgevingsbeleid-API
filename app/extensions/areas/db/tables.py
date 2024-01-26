import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, deferred, mapped_column

from app.core.db.base import Base


class AreasTable(Base):
    __tablename__ = "areas"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Created_Date: Mapped[datetime]
    Created_By_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))

    Shape: Mapped[Optional[bytes]] = deferred(mapped_column(LargeBinary(), nullable=True))

    Source_UUID: Mapped[uuid.UUID] = mapped_column(unique=True)
    Source_ID: Mapped[Optional[int]]
    Source_Title: Mapped[str]
    Source_Symbol: Mapped[Optional[str]]
    Source_Start_Validity: Mapped[datetime]
    Source_End_Validity: Mapped[datetime]
    Source_Created_Date: Mapped[datetime]
    Source_Modified_Date: Mapped[datetime]

    def __repr__(self) -> str:
        return f"AreasTable(UUID={self.UUID!r}, Title={self.Source_Title!r})"
