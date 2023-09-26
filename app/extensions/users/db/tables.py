from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Unicode
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base
from app.core.db.mixins import HasUUID, SerializerMixin, TimeStamped


class UserBaseColumns(TimeStamped, HasUUID):
    Gebruikersnaam: Mapped[Optional[str]]
    Email: Mapped[str] = mapped_column(Unicode(256), unique=True)
    Rol: Mapped[Optional[str]]
    Is_Active: Mapped[bool] = mapped_column(Boolean, default=False)
    # @todo; do not fetch when not needed
    Wachtwoord: Mapped[Optional[str]]  # = mapped_column(deferred=True)
    Last_Login_Date: Mapped[Optional[datetime]]


class UsersTable(Base, UserBaseColumns, SerializerMixin):
    __tablename__ = "Gebruikers"

    def __repr__(self) -> str:
        return f"UsersTable(UUID={self.UUID!r}, Gebruikersnaam={self.Gebruikersnaam!r})"

    def to_dict_safe(self):
        data: dict = self.to_dict()
        del data["Wachtwoord"]
        return data
