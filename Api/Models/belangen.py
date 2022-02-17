# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Integer, String, Unicode

from Api.Endpoints.base_schema import Base_Schema
from Api.Endpoints.validators import HTML_Validate
from Api.Models.short_schemas import Short_Beleidskeuze_Schema
from Api.Endpoints.references import UUID_Linker_Schema, Reverse_UUID_Reference
from Api.database import CommonMixin, db


class Beleidskeuze_Belangen(db.Model):
    __tablename__ = 'Beleidskeuze_Belangen'

    Beleidskeuze_UUID = Column('Beleidskeuze_UUID', ForeignKey('Beleidskeuzes.UUID'), primary_key=True)
    Belang_UUID = Column('Belang_UUID', ForeignKey('Belangen.UUID'), primary_key=True)
    Koppeling_Omschrijving = Column('Koppeling_Omschrijving', String(collation='SQL_Latin1_General_CP1_CI_AS'))

    Beleidskeuze = relationship("Beleidskeuzes", back_populates="Belangen")
    Belang = relationship("Belangen", back_populates="Beleidskeuzes")


class Belangen(CommonMixin, db.Model):
    __tablename__ = 'Belangen'

    Titel = Column(Unicode(150), nullable=False)
    Omschrijving = Column(Unicode)
    Weblink = Column(Unicode)
    Type = Column(Unicode)

    Created_By_Gebruiker = relationship('Gebruikers', primaryjoin='Belangen.Created_By == Gebruikers.UUID')
    Modified_By_Gebruiker = relationship('Gebruikers', primaryjoin='Belangen.Modified_By == Gebruikers.UUID')
    
    Beleidskeuzes = relationship("Beleidskeuze_Belangen", back_populates="Belang")


class Belangen_Schema(Base_Schema):
    Titel = MM.fields.Str(required=True, obprops=["search_title", "short"])
    Omschrijving = MM.fields.Str(
        missing=None, validate=[HTML_Validate], obprops=["search_description"]
    )
    Weblink = MM.fields.Str(missing=None, obprops=[])
    Type = MM.fields.Str(
        missing=None,
        validate=[
            MM.validate.OneOf(
                ["Nationaal Belang", "Wettelijke Taak & Bevoegdheid"])
        ],
        obprops=["short"],
    )
    Ref_Beleidskeuzes = MM.fields.Nested(
        UUID_Linker_Schema,
        many=True,
        obprops=["referencelist", "excluded_patch", "excluded_post"],
    )

    class Meta(Base_Schema.Meta):
        slug = "belangen"
        table = "Belangen"
        read_only = False
        ordered = True
        searchable = True
        references = {
            "Ref_Beleidskeuzes": Reverse_UUID_Reference(
                "Beleidskeuze_Belangen",
                "Beleidskeuzes",
                "Belang_UUID",
                "Beleidskeuze_UUID",
                "Koppeling_Omschrijving",
                Short_Beleidskeuze_Schema,
            )
        }
        graph_conf = "Titel"
