# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Integer, String, Unicode

from Api.Endpoints.base_schema import Base_Schema
from Api.Endpoints.validators import HTML_Validate
from Api.Models.short_schemas import Short_Beleidskeuze_Schema
from Api.Endpoints.references import UUID_Linker_Schema, Reverse_UUID_Reference, UUID_List_Reference
from Api.database import CommonMixin, db
import Api.Models.ambities


# Beleidsdoelen gaan via Begroting
class Beleidskeuze_Beleidsdoelen(db.Model):
    __tablename__ = "Beleidskeuze_Beleidsdoelen"

    Beleidskeuze_UUID = Column(
        "Beleidskeuze_UUID", ForeignKey("Beleidskeuzes.UUID"), primary_key=True
    )
    Beleidsdoel_UUID = Column(
        "Beleidsdoel_UUID", ForeignKey("Beleidsdoelen.UUID"), primary_key=True
    )
    Koppeling_Omschrijving = Column(
        "Koppeling_Omschrijving", String(collation="SQL_Latin1_General_CP1_CI_AS")
    )

    Beleidskeuze = relationship("Beleidskeuzes", back_populates="Beleidsdoelen")
    Beleidsdoel = relationship("Beleidsdoelen", back_populates="Beleidskeuzes")


class Beleidsdoelen(CommonMixin, db.Model):
    __tablename__ = "Beleidsdoelen"

    Titel = Column(Unicode(150), nullable=False)
    Omschrijving = Column(Unicode)
    Weblink = Column(Unicode)

    Created_By_Gebruiker = relationship(
        "Gebruikers", primaryjoin="Beleidsdoelen.Created_By == Gebruikers.UUID"
    )
    Modified_By_Gebruiker = relationship(
        "Gebruikers", primaryjoin="Beleidsdoelen.Modified_By == Gebruikers.UUID"
    )

    Beleidskeuzes = relationship("Beleidskeuze_Beleidsdoelen", back_populates="Beleidsdoel")
    Ambities = relationship("Beleidsdoel_Ambities", back_populates="Beleidsdoel")


class Beleidsdoelen_Schema(Base_Schema):
    Titel = MM.fields.Str(
        required=True, validate=[HTML_Validate], obprops=["search_title", "short"]
    )
    Omschrijving = MM.fields.Str(
        missing=None, validate=[HTML_Validate], obprops=["search_description"]
    )
    Weblink = MM.fields.Str(missing=None, obprops=[])
    Ambities = MM.fields.Nested(
        UUID_Linker_Schema, many=True, obprops=["referencelist"]
    )
    Ref_Beleidskeuzes = MM.fields.Nested(
        UUID_Linker_Schema,
        many=True,
        obprops=["referencelist"],
    )

    class Meta(Base_Schema.Meta):
        slug = "beleidsdoelen"
        table = "Beleidsdoelen"
        read_only = False
        ordered = True
        searchable = True
        references = {
            "Ambities": UUID_List_Reference(
                "Beleidsdoel_Ambities",
                "Ambities",
                "Beleidsdoel_UUID",
                "Ambitie_UUID",
                "Koppeling_Omschrijving",
                Api.Models.ambities.Ambities_Schema,
            ),
            "Ref_Beleidskeuzes": UUID_List_Reference(
                "Beleidskeuze_Beleidsdoelen",
                "Beleidskeuzes",
                "Beleidsdoel_UUID",
                "Beleidskeuze_UUID",
                "Koppeling_Omschrijving",
                Short_Beleidskeuze_Schema,
            )
        }
        graph_conf = "Titel"
