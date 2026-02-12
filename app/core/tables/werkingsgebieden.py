import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import ForeignKey, LargeBinary, Unicode, Table, Column
from sqlalchemy.orm import Mapped, deferred, mapped_column, relationship

from app.core.db.base import Base


Input_GEO_Werkingsgebieden_Onderverdelingen_Assoc = Table(
    "Input_GEO_Werkingsgebieden_Onderverdelingen",
    Base.metadata,
    Column("Werkingsgebied_UUID", ForeignKey("Input_GEO_Werkingsgebieden.UUID"), primary_key=True),
    Column("Onderverdeling_UUID", ForeignKey("Input_GEO_Onderverdeling.UUID"), primary_key=True),
)


class InputGeoWerkingsgebiedenTable(Base):
    __tablename__ = "Input_GEO_Werkingsgebieden"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Title: Mapped[str]
    Description: Mapped[str] = mapped_column(server_default="")
    Created_Date: Mapped[datetime]

    Onderverdelingen: Mapped[List["InputGeoOnderverdelingenTable"]] = relationship(
        secondary=Input_GEO_Werkingsgebieden_Onderverdelingen_Assoc, back_populates="Werkingsgebieden"
    )

    def __repr__(self) -> str:
        return f"InputGeoWerkingsgebiedenTable(UUID={self.UUID!r}, Title={self.Title!r})"


class InputGeoOnderverdelingenTable(Base):
    __tablename__ = "Input_GEO_Onderverdeling"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Title: Mapped[str]
    Description: Mapped[str] = mapped_column(server_default="")
    Created_Date: Mapped[datetime]

    Symbol: Mapped[Optional[str]]
    Geometry: Mapped[Optional[bytes]] = deferred(mapped_column(LargeBinary(), nullable=True))
    Geometry_Hash: Mapped[str] = mapped_column(Unicode(64))
    GML: Mapped[str] = deferred(mapped_column(Unicode))

    Werkingsgebieden: Mapped[list[InputGeoWerkingsgebiedenTable]] = relationship(
        secondary=Input_GEO_Werkingsgebieden_Onderverdelingen_Assoc,
        back_populates="Onderverdelingen",
    )

    def __repr__(self) -> str:
        return f"InputGeoOnderverdelingTable(UUID={self.UUID!r}, Title={self.Title!r})"


# @todo: Should be removed when the InputGeo is used
# @deprecated
class SourceWerkingsgebiedenTable(Base):
    __tablename__ = "Werkingsgebieden"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    ID: Mapped[int]
    Created_Date: Mapped[datetime]
    Modified_Date: Mapped[datetime]

    Start_Validity: Mapped[datetime] = mapped_column(name="Begin_Geldigheid")
    End_Validity: Mapped[datetime] = mapped_column(name="Eind_Geldigheid")

    Title: Mapped[str] = mapped_column(name="Werkingsgebied")
    SHAPE: Mapped[Optional[bytes]] = deferred(mapped_column(LargeBinary(), nullable=True))
    Geometry_Hash: Mapped[str] = mapped_column(Unicode(64), nullable=True)
    GML: Mapped[str] = deferred(mapped_column(Unicode))
    symbol: Mapped[str] = mapped_column(Unicode(265))

    def __repr__(self) -> str:
        return f"SourceWerkingsgebiedenTable(UUID={self.UUID!r}, Title={self.Title!r})"


# @deprecated
class OnderverdelingTable(Base):
    __tablename__ = "Onderverdeling"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    ID: Mapped[int]

    Title: Mapped[str] = mapped_column(name="Onderverdeling")
    SHAPE: Mapped[Optional[bytes]] = deferred(mapped_column(LargeBinary(), nullable=True))
    symbol: Mapped[str]
    Werkingsgebied: Mapped[str] = mapped_column(Unicode(265))
    UUID_Werkingsgebied: Mapped[uuid.UUID]

    Created_Date: Mapped[datetime]
    Modified_Date: Mapped[datetime]

    Start_Validity: Mapped[datetime] = mapped_column(name="Begin_Geldigheid")
    End_Validity: Mapped[datetime] = mapped_column(name="Eind_Geldigheid")

    def __repr__(self) -> str:
        return f"Onderverdeling(UUID={self.UUID!r}, Title={self.Title!r})"
