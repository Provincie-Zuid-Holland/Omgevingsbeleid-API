# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from Endpoints.base_schema import Base_Schema
from Endpoints.validators import HTML_Validate
from Models.short_schemas import Short_Beleidskeuze_Schema
from Endpoints.references import UUID_Linker_Schema, Reverse_UUID_Reference

from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Integer, String, Unicode
from db import CommonMixin, db


class Beleidskeuze_Beleidsregels_DB_Association(db.Model):
    __tablename__ = 'Beleidskeuze_Beleidsregels'

    Beleidskeuze_UUID = Column('Beleidskeuze_UUID', ForeignKey('Beleidskeuzes.UUID'), primary_key=True)
    Beleidsregel_UUID = Column('Beleidsregel_UUID', ForeignKey('Beleidsregels.UUID'), primary_key=True)
    Koppeling_Omschrijving = Column('Koppeling_Omschrijving', String(collation='SQL_Latin1_General_CP1_CI_AS'))

    Beleidskeuze = relationship("Beleidskeuzes", back_populates="Beleidsregels")
    Beleidsregels = relationship("Beleidsregels", back_populates="Beleidskeuzes")


class Beleidsregels_DB_Schema(CommonMixin, db.Model):
    __tablename__ = 'Beleidsregels'

    Titel = Column(Unicode(500), nullable=False)
    Omschrijving = Column(Unicode)
    Weblink = Column(Unicode)
    Externe_URL = Column(String(300, 'SQL_Latin1_General_CP1_CI_AS'))

    Created_By_Gebruiker = relationship('Gebruikers', primaryjoin='Beleidsregels.Created_By == Gebruikers.UUID')
    Modified_By_Gebruiker = relationship('Gebruikers', primaryjoin='Beleidsregels.Modified_By == Gebruikers.UUID')
    
    Ref_Beleidskeuzes = relationship("Beleidskeuze_Beleidsregels", back_populates="Beleidsregels")


class Beleidsregels_Schema(Base_Schema):
    Titel = MM.fields.Str(
        required=True, validate=[HTML_Validate], obprops=["search_title", "short"]
    )
    Omschrijving = MM.fields.Str(
        missing=None, validate=[HTML_Validate], obprops=["search_description"]
    )
    Weblink = MM.fields.Str(missing=None, obprops=[])
    Externe_URL = MM.fields.Str(missing=None, obprops=[])
    Ref_Beleidskeuzes = MM.fields.Nested(
        UUID_Linker_Schema,
        many=True,
        obprops=["referencelist", "excluded_patch", "excluded_post"],
    )

    class Meta(Base_Schema.Meta):
        slug = "beleidsregels"
        table = "Beleidsregels"
        read_only = False
        ordered = True
        searchable = True
        references = {
            "Ref_Beleidskeuzes": Reverse_UUID_Reference(
                "Beleidskeuze_Beleidsregels",
                "Beleidskeuzes",
                "Beleidsregel_UUID",
                "Beleidskeuze_UUID",
                "Koppeling_Omschrijving",
                Short_Beleidskeuze_Schema,
            )
        }
        graph_conf = "Titel"
