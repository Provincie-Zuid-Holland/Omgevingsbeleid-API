# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from Endpoints.base_schema import Base_Schema

from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Integer, String, Unicode
from db import CommonMixin, db

class Werkingsgebieden_DB_Schema(CommonMixin, db.Model):
    __tablename__ = 'Werkingsgebieden'

    Werkingsgebied = Column(Unicode, nullable=False)
    symbol = Column(Unicode(265))

    Created_By_Gebruiker = relationship('Gebruikers', primaryjoin='Werkingsgebieden.Created_By == Gebruikers.UUID')
    Modified_By_Gebruiker = relationship('Gebruikers', primaryjoin='Werkingsgebieden.Modified_By == Gebruikers.UUID')


class Werkingsgebieden_Schema(Base_Schema):
    Werkingsgebied = MM.fields.Str(required=True, obprops=["short"])
    symbol = MM.fields.Str(missing=None, obprops=["short"])

    class Meta(Base_Schema.Meta):
        slug = "werkingsgebieden"
        table = "Werkingsgebieden"
        read_only = True
        ordered = True
        searchable = False
