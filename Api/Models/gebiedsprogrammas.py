# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from Api.Endpoints.status_data_manager import StatusDataManager
import marshmallow as MM
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, String, Unicode

from Api.Endpoints.validators import HTML_Validate
from Api.Endpoints.base_schema import Base_Schema
from Api.Endpoints.references import Reverse_UUID_Reference
from Api.Endpoints.werkingsgebieden_data_manager import WerkingsgebiedenDataManager
from Api.Models.short_schemas import Short_Beleidskeuze_Schema
from Api.database import CommonMixin, db
from Api.Models.maatregelen import Maatregelen_Schema
from Api.Endpoints.references import (
    UUID_Reference,
    UUID_List_Reference,
    UUID_Linker_Schema,
    Reverse_UUID_Reference,
)


class Maatregel_Gebiedsprogrammas(db.Model):
    __tablename__ = "Maatregel_Gebiedsprogrammas"

    Maatregel_UUID = Column(
        "Maatregel_UUID", ForeignKey("Maatregelen.UUID"), primary_key=True
    )
    Gebiedsprogramma_UUID = Column(
        "Gebiedsprogramma_UUID", ForeignKey("Gebiedsprogrammas.UUID"), primary_key=True
    )
    Koppeling_Omschrijving = Column(
        "Koppeling_Omschrijving", String(collation="SQL_Latin1_General_CP1_CI_AS")
    )

    Maatregel = relationship("Maatregelen", back_populates="Gebiedsprogrammas")
    Gebiedsprogramma = relationship("Gebiedsprogrammas", back_populates="Maatregelen")


class Gebiedsprogrammas(CommonMixin, db.Model):
    __tablename__ = "Gebiedsprogrammas"

    Status = Column(Unicode(50), nullable=False)
    Titel = Column(Unicode(150), nullable=False)
    Omschrijving = Column(Unicode)
    Afbeelding = Column(Unicode)

    Created_By_Gebruiker = relationship(
        "Gebruikers", primaryjoin="Gebiedsprogrammas.Created_By == Gebruikers.UUID"
    )
    Modified_By_Gebruiker = relationship(
        "Gebruikers", primaryjoin="Gebiedsprogrammas.Modified_By == Gebruikers.UUID"
    )

    Maatregelen = relationship(
        "Maatregel_Gebiedsprogrammas", back_populates="Gebiedsprogramma"
    )


status_options = [
    "Definitief ontwerp GS",
    "Definitief ontwerp GS concept",
    "Definitief ontwerp PS",
    "Niet-Actief",
    "Ontwerp GS",
    "Ontwerp GS Concept",
    "Ontwerp in inspraak",
    "Ontwerp PS",
    "Uitgecheckt",
    "Vastgesteld",
    "Vigerend",
    "Vigerend gearchiveerd",
]


class Gebiedsprogrammas_Schema(Base_Schema):
    Status = MM.fields.Str(
        required=True, validate=[MM.validate.OneOf(status_options)], obprops=["short"]
    )
    Titel = MM.fields.Str(
        required=True, validate=[HTML_Validate], obprops=["search_title", "short"]
    )
    Omschrijving = MM.fields.Str(missing=None, validate=[HTML_Validate], obprops=[])
    Afbeelding = MM.fields.Str(missing=None, obprops=[])

    Maatregelen = MM.fields.Nested(
        UUID_Linker_Schema, many=True, obprops=["referencelist"]
    )

    class Meta(Base_Schema.Meta):
        slug = "gebiedsprogrammas"
        table = "Gebiedsprogrammas"
        read_only = False
        ordered = True
        searchable = False
        references = {
            "Maatregelen": UUID_List_Reference(
                "Maatregel_Gebiedsprogrammas",
                "Maatregelen",
                "Gebiedsprogramma_UUID",
                "Maatregel_UUID",
                "Koppeling_Omschrijving",
                Maatregelen_Schema,
            ),
        }
        status_conf = ("Status", "Vigerend")
        manager = StatusDataManager
