import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, LargeBinary, String, Unicode
from sqlalchemy.orm import Mapped, deferred, mapped_column, relationship

from app.core.db.base import Base
from app.core.db.mixins import RequireTimeStamped, SerializerMixin, UserMetaData
from app.core.tables.objects import ObjectStaticsTable


class AreasTable(Base):
    __tablename__ = "areas"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    created_date: Mapped[datetime]
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))

    shape: Mapped[bytes | None] = deferred(mapped_column(LargeBinary(), nullable=True))
    gml: Mapped[str] = deferred(mapped_column(String))

    source_uuid: Mapped[uuid.UUID] = mapped_column(unique=True)
    source_id: Mapped[int | None]
    source_title: Mapped[str]
    source_symbol: Mapped[str | None]
    source_start_validity: Mapped[datetime | None]
    source_end_validity: Mapped[datetime | None]
    source_created_date: Mapped[datetime]
    source_modified_date: Mapped[datetime | None]
    source_geometry_index: Mapped[str | None] = mapped_column(Unicode(10), index=True, nullable=True)
    source_geometry_hash: Mapped[str | None] = mapped_column(Unicode(64), nullable=True)

    def __repr__(self) -> str:
        return f"AreasTable(uuid={self.id!r}, title={self.source_title!r})"


class RelationsTable(Base, SerializerMixin):
    __tablename__ = "relations"

    from_code: Mapped[str] = mapped_column(ForeignKey("object_statics.code"), primary_key=True)
    to_code: Mapped[str] = mapped_column(ForeignKey("object_statics.code"), primary_key=True)
    description: Mapped[str]

    from_object_statics: Mapped[ObjectStaticsTable] = relationship(
        ObjectStaticsTable,
        foreign_keys=[from_code],
    )

    to_object_statics: Mapped[ObjectStaticsTable] = relationship(
        ObjectStaticsTable,
        foreign_keys=[to_code],
    )

    def __repr__(self) -> str:
        return f"Relations(from_code={self.from_code!r}, to_code={self.to_code!r})"

    def set_codes(self, code_a: str, code_b: str):
        from_code, to_code = sorted([code_a, code_b])
        self.from_code = from_code
        self.to_code = to_code

    @staticmethod
    def create(description: str, code_a: str, code_b: str) -> "RelationsTable":
        relation: RelationsTable = RelationsTable(
            description=description,
        )
        relation.set_codes(code_a, code_b)
        return relation


class AssetsTable(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    created_date: Mapped[datetime]
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))

    # Lookup for faster access
    lookup: Mapped[str] = mapped_column(Unicode(10), index=True)

    # Hash to confirm uniqueness
    hash: Mapped[str] = mapped_column(Unicode(64))

    # Meta information about the asset, like it is an image
    meta: Mapped[str]

    # Base64 content of the file (might be binary later?)
    content: Mapped[str]

    def __repr__(self) -> str:
        return f"Assets(id={self.id!r})"


class ChangeLogTable(Base):
    __tablename__ = "change_log"

    id: Mapped[int] = mapped_column(primary_key=True)

    object_type: Mapped[str | None] = mapped_column(Unicode(25))
    object_id: Mapped[int | None]

    created_date: Mapped[datetime]
    created_by_id: Mapped[uuid.UUID]  # Explicit NO foreign key here, this is just a log

    action_type: Mapped[str] = mapped_column(Unicode)
    action_data: Mapped[str | None] = mapped_column(Unicode)
    before: Mapped[str | None] = mapped_column(Unicode)
    after: Mapped[str | None] = mapped_column(Unicode)

    change_log_object_type_id = Index("change_log_action_type_id", "action_type", "object_type", "object_id")

    def __repr__(self) -> str:
        return f"ChangeLog(id={self.id!r})"


class StorageFileTable(Base):
    __tablename__ = "storage_files"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    # Lookup for faster access
    lookup: Mapped[str] = mapped_column(Unicode(10), index=True)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    filename: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    content_type: Mapped[str] = mapped_column(Unicode(64), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    binary: Mapped[bytes] = deferred(mapped_column(LargeBinary(), nullable=False))

    created_date: Mapped[datetime]
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))

    def __repr__(self) -> str:
        return f"StorageFileTable(id={self.id!r}, filename={self.filename!r})"


class ObjectRelatedFileTable(Base):
    __tablename__ = "object_related_files"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(Unicode(35), ForeignKey("object_statics.code"), index=True)

    file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("storage_files.id"))

    title: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    created_date: Mapped[datetime]
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))

    # Relationships
    object_statics: Mapped["ObjectStaticsTable"] = relationship()
    file: Mapped["StorageFileTable"] = relationship()

    def __repr__(self) -> str:
        return f"ObjectRelatedFileTable(id={self.id!r}, code={self.code!r})"


class HoofdlijnTable(Base, RequireTimeStamped, UserMetaData, SerializerMixin):
    __tablename__ = "hoofdlijnen"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    type: Mapped[str] = mapped_column(Unicode(255), nullable=False)

    __table_args__ = (Index("ix_hoofdlijnen_name_type", "name", "type", unique=True),)

    def __repr__(self) -> str:
        return f"HoofdlijnTable(id={self.id!r}, name={self.name!r}, type={self.type!r})"
