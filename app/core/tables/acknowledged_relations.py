import uuid
from datetime import UTC, datetime

from sqlalchemy import ForeignKey, and_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base
from app.core.db.mixins import TimeStamped, UserMetaData
from app.core.types import AcknowledgedRelationSide


class AcknowledgedRelationsTable(Base, TimeStamped, UserMetaData):
    __tablename__ = "acknowledged_relations"

    version: Mapped[int] = mapped_column(default=1, nullable=False, primary_key=True)
    requested_by_code: Mapped[str] = mapped_column(ForeignKey("object_statics.Code"))
    from_code: Mapped[str] = mapped_column(ForeignKey("object_statics.Code"), primary_key=True)
    from_acknowledged: Mapped[datetime | None]
    from_acknowledged_by_uuid: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("Gebruikers.UUID"))
    from_explanation: Mapped[str] = mapped_column(default="")

    to_code: Mapped[str] = mapped_column(ForeignKey("object_statics.Code"), primary_key=True)
    to_acknowledged: Mapped[datetime | None] = mapped_column(nullable=True)
    to_acknowledged_by_uuid: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("Gebruikers.UUID"))
    to_explanation: Mapped[str] = mapped_column(default="")

    denied: Mapped[datetime | None]
    deleted_at: Mapped[datetime | None]

    @hybrid_property
    def side_from(self) -> AcknowledgedRelationSide:
        return AcknowledgedRelationSide(
            object_id=self.from_object_id,
            object_type=self.from_object_type,
            acknowledged=self.from_acknowledged,
            acknowledged_by_uuid=self.from_acknowledged_by_uuid,
            title=self.from_title,
            explanation=self.from_explanation,
        )

    @hybrid_property
    def side_to(self) -> AcknowledgedRelationSide:
        return AcknowledgedRelationSide(
            object_id=self.to_object_id,
            object_type=self.to_object_type,
            acknowledged=self.to_acknowledged,
            acknowledged_by_uuid=self.to_acknowledged_by_uuid,
            title=self.to_title,
            explanation=self.to_explanation,
        )

    def get_side(self, code: str) -> AcknowledgedRelationSide:
        if code == self.from_code:
            return self.side_from
        elif code == self.to_code:
            return self.side_to
        else:
            raise RuntimeError("Code does not belong to this acknowledged relation")

    def _assign_side(self, side: AcknowledgedRelationSide, prefix: str):
        setattr(self, f"{prefix}_code", side.code)
        setattr(self, f"{prefix}_acknowledged", side.acknowledged_date)
        setattr(self, f"{prefix}_acknowledged_by_uuid", side.acknowledged_by_uuid)
        setattr(self, f"{prefix}_explanation", side.explanation)

    def with_sides(self, side_a: AcknowledgedRelationSide, side_b: AcknowledgedRelationSide):
        from_side, to_side = sorted([side_a, side_b], key=lambda x: x.code)
        self._assign_side(from_side, "from")
        self._assign_side(to_side, "to")

    def apply_side(self, side: AcknowledgedRelationSide):
        if side.code == self.from_code:
            self._assign_side(side, "from")
        elif side.code == self.to_code:
            self._assign_side(side, "to")
        else:
            raise RuntimeError("Code does not belong to this acknowledged relation")

    def deny(self):
        if self.denied is not None:
            return
        self.denied = datetime.now(UTC)

    def delete(self):
        if self.is_deleted:
            return
        self.deleted_at = datetime.now(UTC)

    # dynamic property for better ORM filtering.
    @hybrid_property
    def is_acknowledged(self) -> bool:
        if self.is_denied:
            return False
        return self.from_acknowledged is not None and self.to_acknowledged is not None

    @is_acknowledged.expression
    def is_acknowledged(cls):
        return and_(
            cls.denied.is_(None),
            cls.from_acknowledged.isnot(None),
            cls.to_acknowledged.isnot(None),
        )

    @hybrid_property
    def is_denied(self) -> bool:
        return self.denied is not None

    @is_denied.expression
    def is_denied(cls):
        return cls.denied.isnot(None)

    @hybrid_property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @is_deleted.expression
    def is_deleted(cls):
        return cls.deleted_at.isnot(None)

    @hybrid_property
    def from_object_type(self) -> str:
        object_type, _ = self.from_code.split("-", 1)
        return object_type

    @hybrid_property
    def from_object_id(self) -> int:
        _, object_id = self.from_code.split("-", 1)
        return int(object_id)

    @hybrid_property
    def to_object_type(self) -> str:
        object_type, _ = self.to_code.split("-", 1)
        return object_type

    @hybrid_property
    def to_object_id(self) -> int:
        _, object_id = self.to_code.split("-", 1)
        return int(object_id)

    @hybrid_property
    def from_title(self):
        return getattr(self.from_object_statics, "Cached_Title", None)

    @hybrid_property
    def to_title(self):
        return getattr(self.to_object_statics, "Cached_Title", None)

    from_object_statics = relationship(
        "ObjectStaticsTable",
        primaryjoin="AcknowledgedRelationsTable.from_code == ObjectStaticsTable.Code",
        lazy="select",
    )
    to_object_statics = relationship(
        "ObjectStaticsTable",
        primaryjoin="AcknowledgedRelationsTable.to_code == ObjectStaticsTable.Code",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"AcknowledgedRelations(from_code={self.from_code!r}, to_code={self.to_code!r}, ack={self.from_acknowledged and self.to_acknowledged})"
