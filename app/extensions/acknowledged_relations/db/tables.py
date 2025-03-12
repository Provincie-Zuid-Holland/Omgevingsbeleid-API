import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import ForeignKey, and_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base
from app.core.db.mixins import TimeStamped, UserMetaData
from app.extensions.acknowledged_relations.models.models import AcknowledgedRelationSide


class AcknowledgedRelationBaseColumns(TimeStamped, UserMetaData):
    Version: Mapped[int] = mapped_column(default=1, nullable=False, primary_key=True)
    Requested_By_Code: Mapped[str] = mapped_column(ForeignKey("object_statics.Code"))
    From_Code: Mapped[str] = mapped_column(ForeignKey("object_statics.Code"), primary_key=True)
    From_Acknowledged: Mapped[Optional[datetime]]
    From_Acknowledged_By_UUID: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("Gebruikers.UUID"))
    From_Explanation: Mapped[str] = mapped_column(default="")

    To_Code: Mapped[int] = mapped_column(ForeignKey("object_statics.Code"), primary_key=True)
    To_Acknowledged: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    To_Acknowledged_By_UUID: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("Gebruikers.UUID"))
    To_Explanation: Mapped[str] = mapped_column(default="")

    Denied: Mapped[Optional[datetime]]
    Deleted_At: Mapped[Optional[datetime]]


class AcknowledgedRelationColumns(AcknowledgedRelationBaseColumns):
    """
    Mapping of relation sides using hybrid method/properties.
    """

    @hybrid_property
    def side_from(self) -> AcknowledgedRelationSide:
        return AcknowledgedRelationSide(
            Object_ID=self.From_Object_ID,
            Object_Type=self.From_Object_Type,
            Acknowledged=self.From_Acknowledged,
            Acknowledged_By_UUID=self.From_Acknowledged_By_UUID,
            Title=self.From_Title,
            Explanation=self.From_Explanation,
        )

    @hybrid_property
    def side_to(self) -> AcknowledgedRelationSide:
        return AcknowledgedRelationSide(
            Object_ID=self.To_Object_ID,
            Object_Type=self.To_Object_Type,
            Acknowledged=self.To_Acknowledged,
            Acknowledged_By_UUID=self.To_Acknowledged_By_UUID,
            Title=self.To_Title,
            Explanation=self.To_Explanation,
        )

    def get_side(self, code: str) -> AcknowledgedRelationSide:
        if code == self.From_Code:
            return self.side_from
        elif code == self.To_Code:
            return self.side_to
        else:
            self._raise_invalid_code()

    def _assign_side(self, side: AcknowledgedRelationSide, prefix: str):
        setattr(self, f"{prefix}_Code", side.Code)
        setattr(self, f"{prefix}_Acknowledged", side.Acknowledged_Date)
        setattr(self, f"{prefix}_Acknowledged_By_UUID", side.Acknowledged_By_UUID)
        setattr(self, f"{prefix}_Explanation", side.Explanation)

    def with_sides(self, side_a: AcknowledgedRelationSide, side_b: AcknowledgedRelationSide):
        from_side, to_side = sorted([side_a, side_b], key=lambda x: x.Code)
        self._assign_side(from_side, "From")
        self._assign_side(to_side, "To")

    def apply_side(self, side: AcknowledgedRelationSide):
        if side.Code == self.From_Code:
            self._assign_side(side, "From")
        elif side.Code == self.To_Code:
            self._assign_side(side, "To")
        else:
            self._raise_invalid_code()

    def deny(self):
        if self.Denied is not None:
            return
        self.Denied = datetime.now(timezone.utc)

    def delete(self):
        if self.Is_Deleted:
            return
        self.Deleted_At = datetime.now(timezone.utc)

    # dynamic property for better ORM filtering.
    @hybrid_property
    def Is_Acknowledged(self) -> bool:
        if self.Is_Denied:
            return False
        return self.From_Acknowledged is not None and self.To_Acknowledged is not None

    @Is_Acknowledged.expression
    def Is_Acknowledged(cls):
        return and_(
            cls.Denied.is_(None),
            cls.From_Acknowledged.isnot(None),
            cls.To_Acknowledged.isnot(None),
        )

    @hybrid_property
    def Is_Denied(self) -> bool:
        return self.Denied is not None

    @Is_Denied.expression
    def Is_Denied(cls):
        return cls.Denied.isnot(None)

    @hybrid_property
    def Is_Deleted(self) -> bool:
        return self.Deleted_At is not None

    @Is_Deleted.expression
    def Is_Deleted(cls):
        return cls.Deleted_At.isnot(None)

    @hybrid_property
    def From_Object_Type(self) -> str:
        object_type, object_id = self.From_Code.split("-", 1)
        return object_type

    @hybrid_property
    def From_Object_ID(self) -> int:
        object_type, object_id = self.From_Code.split("-", 1)
        return object_id

    @hybrid_property
    def To_Object_Type(self) -> str:
        object_type, object_id = self.To_Code.split("-", 1)
        return object_type

    @hybrid_property
    def To_Object_ID(self) -> int:
        object_type, object_id = self.To_Code.split("-", 1)
        return object_id

    @hybrid_property
    def From_Title(self):
        return getattr(self.From_ObjectStatics, "Cached_Title", None)

    @hybrid_property
    def To_Title(self):
        return getattr(self.To_ObjectStatics, "Cached_Title", None)


class AcknowledgedRelationsTable(Base, AcknowledgedRelationColumns):
    __tablename__ = "acknowledged_relations"

    From_ObjectStatics = relationship(
        "ObjectStaticsTable",
        primaryjoin="AcknowledgedRelationsTable.From_Code == ObjectStaticsTable.Code",
        lazy="select",
    )
    To_ObjectStatics = relationship(
        "ObjectStaticsTable",
        primaryjoin="AcknowledgedRelationsTable.To_Code == ObjectStaticsTable.Code",
        lazy="select",
    )

    @staticmethod
    def _raise_invalid_code():
        raise RuntimeError("Code does not belong to this acknowledged relation")

    def __repr__(self) -> str:
        return f"AcknowledgedRelations(From_Code={self.From_Code!r}, To_Code={self.To_Code!r}, Ack={self.From_Acknowledged and self.To_Acknowledged})"
