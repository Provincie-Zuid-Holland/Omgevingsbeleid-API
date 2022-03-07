# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from sqlalchemy.orm import relationship, deferred
from sqlalchemy import Column, ForeignKey, Unicode

from Api.Utils.sqlalchemy import Geometry
from Api.database import CommonMixin, db


class Onderverdeling(CommonMixin, db.Model):
    __tablename__ = 'Onderverdeling'

    Onderverdeling = Column(Unicode, nullable=False)
    symbol = Column(Unicode(265)) # @todo: length feels like a typo
    Werkingsgebied = Column(Unicode(256))
    UUID_Werkingsgebied = Column(ForeignKey('Werkingsgebieden.UUID'), nullable=False)
    SHAPE = deferred(Column(Geometry, nullable=False))

    Created_By_Gebruiker = relationship('Gebruikers', primaryjoin='Onderverdeling.Created_By == Gebruikers.UUID')
    Modified_By_Gebruiker = relationship('Gebruikers', primaryjoin='Onderverdeling.Modified_By == Gebruikers.UUID')

    Ref_Werkingsgebied = relationship('Werkingsgebieden', primaryjoin='Onderverdeling.UUID_Werkingsgebied == Werkingsgebieden.UUID')
