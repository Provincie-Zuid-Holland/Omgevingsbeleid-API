import uuid

from sqlalchemy import ForeignKey, String, Unicode
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base
from app.core.db.mixins import SerializerMixin

IS_ACTIVE = "Actief"


class UsersTable(Base, SerializerMixin):
    __tablename__ = "Gebruikers"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Gebruikersnaam: Mapped[str | None]
    Email: Mapped[str] = mapped_column(Unicode(256), unique=True)
    Rol: Mapped[str | None] = mapped_column(Unicode(100), nullable=True)
    Status: Mapped[str | None]

    user_roles: Mapped[list["UserRoleTable"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    Roles: AssociationProxy[list[str]] = association_proxy(
        "user_roles", "role", creator=lambda role: UserRoleTable(role=role)
    )

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


class UserRoleTable(Base):
    __tablename__ = "user_roles"

    user_uuid: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"), primary_key=True)
    role: Mapped[str] = mapped_column(String(100), primary_key=True)

    user: Mapped["UsersTable"] = relationship(back_populates="user_roles")
