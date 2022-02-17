# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Integer, String, Unicode

from Api.Endpoints.base_schema import Base_Schema
from Api.Endpoints.references import Reverse_UUID_Reference
from Api.Models.short_schemas import Short_Beleidskeuze_Schema
from Api.database import CommonMixin, db
from Api.Utils.sqlalchemy import Geometry


class Beleidskeuze_Werkingsgebieden(db.Model):
    __tablename__ = 'Beleidskeuze_Werkingsgebieden'

    Beleidskeuze_UUID = Column('Beleidskeuze_UUID', ForeignKey('Beleidskeuzes.UUID'), primary_key=True)
    Werkingsgebied_UUID = Column('Werkingsgebied_UUID', ForeignKey('Werkingsgebieden.UUID'), primary_key=True)
    Koppeling_Omschrijving = Column('Koppeling_Omschrijving', String(collation='SQL_Latin1_General_CP1_CI_AS'))

    Beleidskeuze = relationship("Beleidskeuzes", back_populates="Werkingsgebieden")
    Werkingsgebied = relationship("Werkingsgebieden", back_populates="Beleidskeuzes")


class Werkingsgebieden(CommonMixin, db.Model):
    __tablename__ = 'Werkingsgebieden'

    Werkingsgebied = Column(Unicode, nullable=False)
    symbol = Column(Unicode(265))
    SHAPE = Column(Geometry, nullable=False)

    Created_By_Gebruiker = relationship('Gebruikers', primaryjoin='Werkingsgebieden.Created_By == Gebruikers.UUID')
    Modified_By_Gebruiker = relationship('Gebruikers', primaryjoin='Werkingsgebieden.Modified_By == Gebruikers.UUID')
    
    Beleidskeuzes = relationship("Beleidskeuze_Werkingsgebieden", back_populates="Werkingsgebied")


class Werkingsgebieden_Schema(Base_Schema):
    Werkingsgebied = MM.fields.Str(required=True, obprops=["short"])
    symbol = MM.fields.Str(missing=None, obprops=["short"])

    class Meta(Base_Schema.Meta):
        slug = "werkingsgebieden"
        table = "Werkingsgebieden"
        read_only = True
        ordered = True
        searchable = False
        references = {
            "Ref_Beleidskeuzes": Reverse_UUID_Reference(
                "Beleidskeuze_Werkingsgebieden",
                "Beleidskeuzes",
                "Werkingsgebied_UUID",
                "Beleidskeuze_UUID",
                "Koppeling_Omschrijving",
                Short_Beleidskeuze_Schema,
            )
        }
