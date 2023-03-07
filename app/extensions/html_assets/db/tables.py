from datetime import datetime
import uuid

from sqlalchemy import ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base


class AssetsTable(Base):
    __tablename__ = "assets"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Created_Date: Mapped[datetime]
    Created_By_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))

    # Hash to confirm uniqueness
    Hash: Mapped[str]

    # Meta information about the asset, like it is an image
    Meta: Mapped[str]

    # Base64 content of the file (might be binary later?)
    Content: Mapped[str]

    __table_args__ = (Index("Hash", func.substr(1, 10)),)

    def __repr__(self) -> str:
        return f"Assets(UUID={self.UUID!r})"
