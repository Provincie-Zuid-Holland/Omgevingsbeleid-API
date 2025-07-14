import uuid
from typing import Optional

from sqlalchemy import Unicode
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base
from app.core.db.mixins import SerializerMixin

IS_ACTIVE = "Actief"


class UsersTable(Base, SerializerMixin):
    __tablename__ = "Gebruikers"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Gebruikersnaam: Mapped[Optional[str]]
    Email: Mapped[str] = mapped_column(Unicode(256), unique=True)
    Rol: Mapped[Optional[str]]
    Status: Mapped[Optional[str]]

    # @todo: move to separate table
    Wachtwoord: Mapped[Optional[str]]  # = mapped_column(deferred=True)

    @property
    def IsActive(self) -> bool:
        return self.Status == IS_ACTIVE

    def __repr__(self) -> str:
        return f"UsersTable(UUID={self.UUID!r}, Gebruikersnaam={self.Gebruikersnaam!r})"

    def to_dict_safe(self):
        data: dict = self.to_dict()
        del data["Wachtwoord"]
        return data
