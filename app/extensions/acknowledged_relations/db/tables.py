from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base
from app.core.db.mixins import TimeStamped, UserMetaData
from app.extensions.acknowledged_relations.models.models import (
    AcknowledgedRelation,
    AcknowledgedRelationSide,
)


class AcknowledgedRelationBaseColumns(TimeStamped, UserMetaData):
    Requested_By_Code: Mapped[str] = mapped_column(
        ForeignKey("object_statics.Code"), primary_key=True
    )

    From_Code: Mapped[str] = mapped_column(
        ForeignKey("object_statics.Code"), primary_key=True
    )
    From_Acknowledged: Mapped[bool]
    From_Acknowledged_Date: Mapped[Optional[datetime]]
    From_Acknowledged_By_UUID: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("Gebruikers.UUID")
    )
    From_Title: Mapped[str] = mapped_column(default="")
    From_Explanation: Mapped[str] = mapped_column(default="")

    To_Code: Mapped[int] = mapped_column(
        ForeignKey("object_statics.Code"), primary_key=True
    )
    To_Acknowledged: Mapped[bool]
    To_Acknowledged_Date: Mapped[Optional[datetime]]
    To_Acknowledged_By_UUID: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("Gebruikers.UUID")
    )
    To_Title: Mapped[str] = mapped_column(default="")
    To_Explanation: Mapped[str] = mapped_column(default="")


class AcknowledgedRelationColumns(AcknowledgedRelationBaseColumns):
    def with_sides(
        self, side_a: AcknowledgedRelationSide, side_b: AcknowledgedRelationSide
    ):
        from_side, to_side = sorted([side_a, side_b], key=lambda x: x.Code)

        self.From_Code = from_side.Code
        self.From_Acknowledged = from_side.Acknowledged
        self.From_Acknowledged_Date = from_side.Acknowledged_Date
        self.From_Acknowledged_By_UUID = from_side.Acknowledged_By_UUID
        self.From_Title = from_side.Title
        self.From_Explanation = from_side.Explanation

        self.To_Code = to_side.Code
        self.To_Acknowledged = to_side.Acknowledged
        self.To_Acknowledged_Date = to_side.Acknowledged_Date
        self.To_Acknowledged_By_UUID = to_side.Acknowledged_By_UUID
        self.To_Title = to_side.Title
        self.To_Explanation = to_side.Explanation

    def apply_side(self, side: AcknowledgedRelationSide):
        if side.Code == self.From_Code:
            self.From_Code = side.Code
            self.From_Acknowledged = side.Acknowledged
            self.From_Acknowledged_Date = side.Acknowledged_Date
            self.From_Acknowledged_By_UUID = side.Acknowledged_By_UUID
            self.From_Title = side.Title
            self.From_Explanation = side.Explanation
        elif side.Code == self.To_Code:
            self.To_Code = side.Code
            self.To_Acknowledged = side.Acknowledged
            self.To_Acknowledged_Date = side.Acknowledged_Date
            self.To_Acknowledged_By_UUID = side.Acknowledged_By_UUID
            self.To_Title = side.Title
            self.To_Explanation = side.Explanation
        else:
            self._raise_invalid_code()

    def get_side(self, code: str) -> AcknowledgedRelationSide:
        object_type, object_id = code.split("-", 1)
        if code == self.From_Code:
            return AcknowledgedRelationSide(
                Object_ID=int(object_id),
                Object_Type=object_type,
                Acknowledged=self.From_Acknowledged,
                Acknowledged_Date=self.From_Acknowledged_Date,
                Acknowledged_By_UUID=self.From_Acknowledged_By_UUID,
                Title=self.From_Title,
                Explanation=self.From_Explanation,
            )
        elif code == self.To_Code:
            return AcknowledgedRelationSide(
                Object_ID=int(object_id),
                Object_Type=object_type,
                Acknowledged=self.To_Acknowledged,
                Acknowledged_Date=self.To_Acknowledged_Date,
                Acknowledged_By_UUID=self.To_Acknowledged_By_UUID,
                Title=self.To_Title,
                Explanation=self.To_Explanation,
            )
        self._raise_invalid_code()

    def as_model(self, perspective_code: str) -> AcknowledgedRelation:
        """
        perspective is who requested this and will be used as the "Side_A" side
        """
        side_from: AcknowledgedRelationSide = self.get_side(self.From_Code)
        side_to: AcknowledgedRelationSide = self.get_side(self.To_Code)

        if perspective_code == side_from.Code:
            side_a, side_b = side_from, side_to
        else:
            side_a, side_b = side_to, side_from

        return AcknowledgedRelation(
            Side_A=side_a,
            Side_B=side_b,
            Requested_By_Code=self.Requested_By_Code,
            Created_Date=self.Created_Date,
            Created_By_UUID=self.Created_By_UUID,
            Modified_Date=self.Modified_Date,
            Modified_By_UUID=self.Modified_By_UUID,
        )


class AcknowledgedRelationsTable(Base, AcknowledgedRelationColumns):
    __tablename__ = "acknowledged_relations"

    @staticmethod
    def _raise_invalid_code():
        raise RuntimeError("Code does not belong to this acknowledged relation")

    def __repr__(self) -> str:
        return f"AcknowledgedRelations(From_Code={self.From_Code!r}, To_Code={self.To_Code!r}, Ack={self.From_Acknowledged and self.To_Acknowledged})"
