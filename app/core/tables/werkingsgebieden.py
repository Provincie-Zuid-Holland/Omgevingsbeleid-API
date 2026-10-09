import uuid
from datetime import datetime

from sqlalchemy import Column, ForeignKey, LargeBinary, Table, Unicode
from sqlalchemy.orm import Mapped, deferred, mapped_column, relationship

from app.core.db.base import Base

Input_GEO_Werkingsgebieden_Onderverdelingen_Assoc = Table(
    "input_geo_werkingsgebieden_onderverdelingen",
    Base.metadata,
    Column("werkingsgebied_id", ForeignKey("input_geo_werkingsgebieden.id"), primary_key=True),
    Column("onderverdeling_id", ForeignKey("input_geo_onderverdeling.id"), primary_key=True),
)


class InputGeoWerkingsgebiedenTable(Base):
    __tablename__ = "input_geo_werkingsgebieden"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str] = mapped_column(server_default="")
    created_date: Mapped[datetime]

    onderverdelingen: Mapped[list["InputGeoOnderverdelingenTable"]] = relationship(
        secondary=Input_GEO_Werkingsgebieden_Onderverdelingen_Assoc,
        back_populates="werkingsgebieden",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"InputGeoWerkingsgebiedenTable(id={self.id!r}, title={self.title!r})"


class InputGeoOnderverdelingenTable(Base):
    __tablename__ = "input_geo_onderverdeling"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str] = mapped_column(server_default="")
    created_date: Mapped[datetime]

    symbol: Mapped[str | None]
    geometry: Mapped[bytes | None] = deferred(mapped_column(LargeBinary(), nullable=True))
    geometry_hash: Mapped[str] = mapped_column(Unicode(64))
    gml: Mapped[str] = deferred(mapped_column(Unicode))

    werkingsgebieden: Mapped[list[InputGeoWerkingsgebiedenTable]] = relationship(
        secondary=Input_GEO_Werkingsgebieden_Onderverdelingen_Assoc,
        back_populates="onderverdelingen",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"InputGeoOnderverdelingTable(id={self.id!r}, title={self.title!r})"


class InputGeoWerkingsgebiedOnderverdelingTable(Base):
    __table__ = Input_GEO_Werkingsgebieden_Onderverdelingen_Assoc

    def __repr__(self) -> str:
        return (
            f"InputGeoWerkingsgebiedOnderverdelingTable("
            f"werkingsgebied_id={self.werkingsgebied_id!r}, "
            f"onderverdeling_id={self.onderverdeling_id!r})"
        )


# @todo: Should be removed when the InputGeo is used
# @deprecated
class SourceWerkingsgebiedenTable(Base):
    __tablename__ = "werkingsgebieden"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    ref_id: Mapped[int]
    created_date: Mapped[datetime]
    modified_date: Mapped[datetime]

    title: Mapped[str]
    shape: Mapped[bytes | None] = deferred(mapped_column(LargeBinary(), nullable=True))
    geometry_hash: Mapped[str] = mapped_column(Unicode(64), nullable=True)
    gml: Mapped[str] = deferred(mapped_column(Unicode))
    symbol: Mapped[str] = mapped_column(Unicode(265))

    def __repr__(self) -> str:
        return f"SourceWerkingsgebiedenTable(id={self.id!r}, title={self.title!r})"


# @deprecated
class OnderverdelingTable(Base):
    __tablename__ = "onderverdeling"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    ref_id: Mapped[int]

    title: Mapped[str] = mapped_column(name="Onderverdeling")
    shape: Mapped[bytes | None] = deferred(mapped_column(LargeBinary(), nullable=True))
    symbol: Mapped[str]
    werkingsgebied: Mapped[str] = mapped_column(Unicode(265))
    werkingsgebied_id: Mapped[uuid.UUID]

    created_date: Mapped[datetime]
    modified_date: Mapped[datetime]

    start_validity: Mapped[datetime]
    end_validity: Mapped[datetime]

    def __repr__(self) -> str:
        return f"Onderverdeling(id={self.id!r}, title={self.title!r})"
