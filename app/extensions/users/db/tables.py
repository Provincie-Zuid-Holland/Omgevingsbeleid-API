from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base
from app.core.db.mixins import HasUUID


class UserBaseColumns(HasUUID):
    Gebruikersnaam: Mapped[Optional[str]]
    Email: Mapped[str] = mapped_column(String(265), unique=True)
    Rol: Mapped[Optional[str]]
    Status: Mapped[Optional[str]]
    # @todo; do not fetch when not needed
    Wachtwoord: Mapped[Optional[str]]  # = mapped_column(deferred=True)

    @property
    def IsActief(self) -> bool:
        return self.Status == "Actief"


class UsersTable(Base, UserBaseColumns):
    __tablename__ = "Gebruikers"

    def __repr__(self) -> str:
        return f"Gebruikers(UUID={self.UUID!r}, Gebruikersnaam={self.Gebruikersnaam!r})"
