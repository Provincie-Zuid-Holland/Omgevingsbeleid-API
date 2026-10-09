import uuid

from sqlalchemy import ForeignKey, String, Unicode
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base
from app.core.db.mixins import SerializerMixin


class UsersTable(Base, SerializerMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str | None]
    email: Mapped[str] = mapped_column(Unicode(256), unique=True)
    role: Mapped[str | None] = mapped_column(Unicode(100), nullable=True)
    is_active: Mapped[bool]

    user_roles: Mapped[list["UserRoleTable"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    roles: AssociationProxy[list[str]] = association_proxy(
        "user_roles", "role", creator=lambda role: UserRoleTable(role=role)
    )

    # @todo: move to separate table
    password_hashed: Mapped[str | None]  # = mapped_column(deferred=True)

    def __repr__(self) -> str:
        return f"UsersTable(id={self.id!r}, name={self.name!r})"

    def to_dict_safe(self):
        data: dict = self.to_dict()
        del data["password_hashed"]
        return data


class UserRoleTable(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(100), primary_key=True)

    user: Mapped["UsersTable"] = relationship(back_populates="user_roles")
