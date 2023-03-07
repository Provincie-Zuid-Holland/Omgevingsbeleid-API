from datetime import datetime
import uuid

from sqlalchemy import ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base


class AssetsTable(Base):
    __tablename__ = "assets"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Created_Date: Mapped[datetime]
    Created_By_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))

    # Lookup for faster access
    Lookup: Mapped[str] = mapped_column(String(10), index=True)

    # Hash to confirm uniqueness
    Hash: Mapped[str] = mapped_column(String(64))

    # Meta information about the asset, like it is an image
    Meta: Mapped[str]

    # Base64 content of the file (might be binary later?)
    Content: Mapped[str]

    def __repr__(self) -> str:
        return f"Assets(UUID={self.UUID!r})"
