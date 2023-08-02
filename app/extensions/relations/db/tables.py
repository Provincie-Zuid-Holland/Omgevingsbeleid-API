from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base
from app.core.db.mixins import SerializerMixin


class RelationsTable(Base, SerializerMixin):
    __tablename__ = "relations"

    From_Code: Mapped[str] = mapped_column(ForeignKey("object_statics.Code"), primary_key=True)
    To_Code: Mapped[int] = mapped_column(ForeignKey("object_statics.Code"), primary_key=True)
    Description: Mapped[str]

    FromObjectStatics: Mapped["ObjectStaticsTable"] = relationship(
        "ObjectStaticsTable",
        foreign_keys=[From_Code],
    )

    ToObjectStatics: Mapped["ObjectStaticsTable"] = relationship(
        "ObjectStaticsTable",
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
