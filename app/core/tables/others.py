import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Index, Integer, LargeBinary, String, Unicode
from sqlalchemy.orm import Mapped, deferred, mapped_column, relationship

from app.core.db.base import Base
from app.core.db.mixins import SerializerMixin
from app.core.tables.objects import ObjectStaticsTable


class AreasTable(Base):
    __tablename__ = "areas"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Created_Date: Mapped[datetime]
    Created_By_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))

    Shape: Mapped[Optional[bytes]] = deferred(mapped_column(LargeBinary(), nullable=True))
    Gml: Mapped[str] = deferred(mapped_column(String))

    Source_UUID: Mapped[uuid.UUID] = mapped_column(unique=True)
    Source_ID: Mapped[Optional[int]]
    Source_Title: Mapped[str]
    Source_Symbol: Mapped[Optional[str]]
    Source_Start_Validity: Mapped[Optional[datetime]]
    Source_End_Validity: Mapped[Optional[datetime]]
    Source_Created_Date: Mapped[datetime]
    Source_Modified_Date: Mapped[Optional[datetime]]
    Source_Geometry_Index: Mapped[Optional[str]] = mapped_column(Unicode(10), index=True, nullable=True)
    Source_Geometry_Hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    def __repr__(self) -> str:
        return f"AreasTable(UUID={self.UUID!r}, Title={self.Source_Title!r})"


class RelationsTable(Base, SerializerMixin):
    __tablename__ = "relations"

    From_Code: Mapped[str] = mapped_column(ForeignKey("object_statics.Code"), primary_key=True)
    To_Code: Mapped[str] = mapped_column(ForeignKey("object_statics.Code"), primary_key=True)
    Description: Mapped[str]

    FromObjectStatics: Mapped[ObjectStaticsTable] = relationship(
        ObjectStaticsTable,
        foreign_keys=[From_Code],
    )

    ToObjectStatics: Mapped[ObjectStaticsTable] = relationship(
        ObjectStaticsTable,
        foreign_keys=[To_Code],
    )

    def __repr__(self) -> str:
        return f"Relations(From_Code={self.From_Code!r}, To_Code={self.To_Code!r})"

    def set_codes(self, code_a: str, code_b: str):
        from_code, to_code = sorted([code_a, code_b])
        self.From_Code = from_code
        self.To_Code = to_code

    @staticmethod
    def create(description: str, code_a: str, code_b: str) -> "RelationsTable":
        relation: RelationsTable = RelationsTable(
            Description=description,
        )
        relation.set_codes(code_a, code_b)
        return relation


class AssetsTable(Base):
    __tablename__ = "assets"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Created_Date: Mapped[datetime]
    Created_By_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))

    # Lookup for faster access
    Lookup: Mapped[str] = mapped_column(Unicode(10), index=True)

    # Hash to confirm uniqueness
    Hash: Mapped[str] = mapped_column(Unicode(64))

    # Meta information about the asset, like it is an image
    Meta: Mapped[str]

    # Base64 content of the file (might be binary later?)
    Content: Mapped[str]

    def __repr__(self) -> str:
        return f"Assets(UUID={self.UUID!r})"


class ChangeLogTable(Base):
    __tablename__ = "change_log"

    ID: Mapped[int] = mapped_column(primary_key=True)

    Object_Type: Mapped[Optional[str]] = mapped_column(Unicode(25))
    Object_ID: Mapped[Optional[int]]

    Created_Date: Mapped[datetime]
    Created_By_UUID: Mapped[uuid.UUID]  # Explicit NO foreign key here, this is just a log

    Action_Type: Mapped[str] = mapped_column(Unicode)
    Action_Data: Mapped[Optional[str]] = mapped_column(Unicode)
    Before: Mapped[Optional[str]] = mapped_column(Unicode)
    After: Mapped[Optional[str]] = mapped_column(Unicode)

    change_log_object_type_id = Index("change_log_action_type_id", "Action_Type", "Object_Type", "Object_ID")

    def __repr__(self) -> str:
        return f"ChangeLog(ID={self.ID!r})"


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
