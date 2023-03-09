import uuid
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base


class GebruikersTable(Base):
    __tablename__ = "Gebruikers"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Gebruikersnaam: Mapped[Optional[str]]
    Email: Mapped[str] = mapped_column(unique=True)
    Rol: Mapped[Optional[str]]
    Status: Mapped[Optional[str]]
    # @todo; do not fetch when not needed
    Wachtwoord: Mapped[Optional[str]]  # = mapped_column(deferred=True)

    @property
    def IsActief(self) -> bool:
        return self.Status == "Actief"

    def __repr__(self) -> str:
        return f"Gebruikers(UUID={self.UUID!r}, Gebruikersnaam={self.Gebruikersnaam!r})"
