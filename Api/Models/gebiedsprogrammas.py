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
from Api.settings import default_user_uuid
from Api.Models.maatregelen import Maatregelen_Schema
import Api.Models.gebruikers
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

    Eigenaar_1 = Column(ForeignKey("Gebruikers.UUID"))
    Eigenaar_2 = Column(ForeignKey("Gebruikers.UUID"))
    Portefeuillehouder_1 = Column(ForeignKey("Gebruikers.UUID"))
    Portefeuillehouder_2 = Column(ForeignKey("Gebruikers.UUID"))
    Opdrachtgever = Column(ForeignKey("Gebruikers.UUID"))

    Status = Column(Unicode(50), nullable=False)
    Titel = Column(Unicode(150), nullable=False)
    Omschrijving = Column(Unicode)
    Afbeelding = Column(Unicode)
    Weblink = Column(Unicode(200))
    Besluitnummer = Column(Unicode)

    Created_By_Gebruiker = relationship(
        "Gebruikers", primaryjoin="Gebiedsprogrammas.Created_By == Gebruikers.UUID"
    )
    Modified_By_Gebruiker = relationship(
        "Gebruikers", primaryjoin="Gebiedsprogrammas.Modified_By == Gebruikers.UUID"
    )

    Maatregelen = relationship(
        "Maatregel_Gebiedsprogrammas", back_populates="Gebiedsprogramma"
    )

    Ref_Eigenaar_1 = relationship(
        "Gebruikers", primaryjoin="Gebiedsprogrammas.Eigenaar_1 == Gebruikers.UUID"
    )
    Ref_Eigenaar_2 = relationship(
        "Gebruikers", primaryjoin="Gebiedsprogrammas.Eigenaar_2 == Gebruikers.UUID"
    )
    Ref_Portefeuillehouder_1 = relationship(
        "Gebruikers",
        primaryjoin="Gebiedsprogrammas.Portefeuillehouder_1 == Gebruikers.UUID",
    )
    Ref_Portefeuillehouder_2 = relationship(
        "Gebruikers",
        primaryjoin="Gebiedsprogrammas.Portefeuillehouder_2 == Gebruikers.UUID",
    )
    Ref_Opdrachtgever = relationship(
        "Gebruikers", primaryjoin="Gebiedsprogrammas.Opdrachtgever == Gebruikers.UUID"
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
    Afbeelding = MM.fields.Str(missing=None, obprops=["short"])

    Maatregelen = MM.fields.Nested(
        UUID_Linker_Schema, many=True, obprops=["referencelist"]
    )

    Eigenaar_1 = MM.fields.UUID(
        missing=default_user_uuid,
        allow_none=True,
        userfield=True,
        obprops=[],
    )
    Eigenaar_2 = MM.fields.UUID(
        missing=default_user_uuid,
        allow_none=True,
        userfield=True,
        obprops=[],
    )
    Portefeuillehouder_1 = MM.fields.UUID(
        missing=default_user_uuid,
        allow_none=True,
        obprops=[],
    )
    Portefeuillehouder_2 = MM.fields.UUID(
        missing=default_user_uuid,
        allow_none=True,
        obprops=[],
    )
    Opdrachtgever = MM.fields.UUID(
        missing=default_user_uuid,
        allow_none=True,
        obprops=[],
    )

    Weblink = MM.fields.Str(missing=None, validate=[HTML_Validate], obprops=[])
    Besluitnummer = MM.fields.Str(missing=None, obprops=[])

    class Meta(Base_Schema.Meta):
        slug = "gebiedsprogrammas"
        table = "Gebiedsprogrammas"
        read_only = False
        ordered = True
        searchable = False
        references = {
            "Eigenaar_1": UUID_Reference(
                "Gebruikers", Api.Models.gebruikers.Gebruikers_Schema
            ),
            "Eigenaar_2": UUID_Reference(
                "Gebruikers", Api.Models.gebruikers.Gebruikers_Schema
            ),
            "Portefeuillehouder_1": UUID_Reference(
                "Gebruikers", Api.Models.gebruikers.Gebruikers_Schema
            ),
            "Portefeuillehouder_2": UUID_Reference(
                "Gebruikers", Api.Models.gebruikers.Gebruikers_Schema
            ),
            "Opdrachtgever": UUID_Reference(
                "Gebruikers", Api.Models.gebruikers.Gebruikers_Schema
            ),
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
        graph_conf = "Titel"
        manager = StatusDataManager
