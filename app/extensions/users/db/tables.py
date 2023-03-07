import uuid
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base


class GebruikersTable(Base):
    __tablename__ = "Gebruikers"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Gebruikersnaam: Mapped[Optional[str]]
    Email: Mapped[str]
    Rol: Mapped[Optional[str]]
    IsActief: Mapped[bool] = mapped_column(default=False)
    # @todo; do not fetch when not needed
    Wachtwoord: Mapped[Optional[str]]  # = mapped_column(deferred=True)

    def __repr__(self) -> str:
        return f"Gebruikers(UUID={self.UUID!r}, Gebruikersnaam={self.Gebruikersnaam!r})"
