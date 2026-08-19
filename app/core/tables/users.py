import uuid

from sqlalchemy import ForeignKey, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.associationproxy import association_proxy

from app.core.db.base import Base
from app.core.db.mixins import SerializerMixin

IS_ACTIVE = "Actief"


class UsersTable(Base, SerializerMixin):
    __tablename__ = "Gebruikers"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Gebruikersnaam: Mapped[str | None]
    Email: Mapped[str] = mapped_column(Unicode(256), unique=True)
    Rol: Mapped[str | None]
    Status: Mapped[str | None]

    user_roles: Mapped[list["UserRoleTable"]] = relationship(
        back_populates="User",
    )
    Roles = association_proxy("user_roles", "Role", creator=lambda role: UserRoleTable(Role=role))
    
    # @todo: move to separate table
    Wachtwoord: Mapped[str | None]  # = mapped_column(deferred=True)

    @property
    def IsActive(self) -> bool:
        return self.Status == IS_ACTIVE

    def __repr__(self) -> str:
        return f"UsersTable(UUID={self.UUID!r}, Gebruikersnaam={self.Gebruikersnaam!r})"

    def to_dict_safe(self):
        data: dict = self.to_dict()
        del data["Wachtwoord"]
        return data

# The only doubt I have is the language of the table name and column names. Since the Gebruikers table is in Dutch but the rest is English
class UserRoleTable(Base):
    __tablename__ = "user_roles"

    User_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"), primary_key=True)
    Role: Mapped[str] = mapped_column(primary_key=True)

    User: Mapped["UsersTable"] = relationship(back_populates="user_roles")
