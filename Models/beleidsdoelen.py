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


class Beleidskeuze_Beleidsdoelen_DB_Association(db.Model):
    __tablename__ = 'Beleidskeuze_Beleidsdoelen'

    Beleidskeuze_UUID = Column('Beleidskeuze_UUID', ForeignKey('Beleidskeuzes.UUID'), primary_key=True)
    Beleidsdoel_UUID = Column('Beleidsdoel_UUID', ForeignKey('Beleidsdoelen.UUID'), primary_key=True)
    Koppeling_Omschrijving = Column('Koppeling_Omschrijving', String(collation='SQL_Latin1_General_CP1_CI_AS'))

    Beleidskeuze = relationship("Beleidskeuzes", back_populates="Beleidsdoelen")
    Beleidsdoel = relationship("Beleidsdoelen", back_populates="Beleidskeuzes")


class Beleidsdoelen_DB_Schema(CommonMixin, db.Model):
    __tablename__ = 'Beleidsdoelen'

    Titel = Column(Unicode(150), nullable=False)
    Omschrijving = Column(Unicode)
    Weblink = Column(Unicode)

    Created_By_Gebruiker = relationship('Gebruikers', primaryjoin='Beleidsdoelen.Created_By == Gebruikers.UUID')
    Modified_By_Gebruiker = relationship('Gebruikers', primaryjoin='Beleidsdoelen.Modified_By == Gebruikers.UUID')
    
    Ref_Beleidskeuzes = relationship("Beleidskeuze_Beleidsdoelen", back_populates="Beleidsdoel")


class Beleidsdoelen_Schema(Base_Schema):
    Titel = MM.fields.Str(
        required=True, validate=[HTML_Validate], obprops=["search_title", "short"]
    )
    Omschrijving = MM.fields.Str(
        missing=None, validate=[HTML_Validate], obprops=["search_description"]
    )
    Weblink = MM.fields.Str(missing=None, obprops=[])
    Ref_Beleidskeuzes = MM.fields.Nested(
        UUID_Linker_Schema,
        many=True,
        obprops=["referencelist", "excluded_patch", "excluded_post"],
    )

    class Meta(Base_Schema.Meta):
        slug = "beleidsdoelen"
        table = "Beleidsdoelen"
        read_only = False
        ordered = True
        searchable = True
        references = {
            "Ref_Beleidskeuzes": Reverse_UUID_Reference(
                "Beleidskeuze_Beleidsdoelen",
                "Beleidskeuzes",
                "Beleidsdoel_UUID",
                "Beleidskeuze_UUID",
                "Koppeling_Omschrijving",
                Short_Beleidskeuze_Schema,
            )
        }
        graph_conf = "Titel"
