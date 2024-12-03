import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, LargeBinary, String, Unicode
from sqlalchemy.orm import Mapped, deferred, mapped_column

from app.core.db.base import Base


class StorageFileTable(Base):
    __tablename__ = "storage_files"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    # Lookup for faster access
    Lookup: Mapped[str] = mapped_column(Unicode(10), index=True)
    Checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    Filename: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    Content_Type: Mapped[str] = mapped_column(Unicode(64), nullable=False)
    Size: Mapped[int] = mapped_column(Integer, nullable=False)
    Binary: Mapped[bytes] = deferred(mapped_column(LargeBinary(), nullable=False))

    Created_Date: Mapped[datetime]
    Created_By_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))

    def __repr__(self) -> str:
        return f"StorageFileTable(UUID={self.UUID!r}, Filename={self.Filename!r})"
