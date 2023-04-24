from datetime import datetime
from typing import List
import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base
from app.extensions.users.db.tables import UsersTable


class RegulationsTable(Base):
    __tablename__ = "regulations"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Created_Date: Mapped[datetime]
    Created_By_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))
    Modified_Date: Mapped[datetime]
    Modified_By_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))
    Title: Mapped[str]
    Type: Mapped[str]

    Created_By: Mapped[List[UsersTable]] = relationship(
        primaryjoin="RegulationsTable.Created_By_UUID == UsersTable.UUID"
    )
    Modified_By: Mapped[List[UsersTable]] = relationship(
        primaryjoin="RegulationsTable.Modified_By_UUID == UsersTable.UUID"
    )

    def __repr__(self) -> str:
        return f"Regulations(UUID={self.UUID!r})"


class ObjectRegulationsTable(Base):
    __tablename__ = "object_regulations"

    Object_Code: Mapped[str] = mapped_column(
        ForeignKey("object_statics.Code"), primary_key=True
    )
    Regulation_UUID: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("regulations.UUID"), primary_key=True
    )

    def __repr__(self) -> str:
        return f"ObjectRegulations(Object_Code={self.Object_Code!r}, Regulation_UUID={self.Regulation_UUID!r})"
