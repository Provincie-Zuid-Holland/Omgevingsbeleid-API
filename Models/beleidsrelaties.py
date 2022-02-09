# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from Endpoints.base_schema import Base_Schema
from Endpoints.references import UUID_Reference
from Endpoints.validators import HTML_Validate
from Models.beleidskeuzes import Beleidskeuzes_Schema
from globals import null_uuid

from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Integer, String, Unicode, DateTime, text
from db import CommonMixin, db

class Beleidsrelaties_DB_Schema(CommonMixin, db.Model):
    __tablename__ = 'Beleidsrelaties'

    Omschrijving = Column(Unicode)
    Status = Column(Unicode(50))
    Aanvraag_Datum = Column(DateTime)
    Datum_Akkoord = Column(DateTime)
    Titel = Column(Unicode(50), nullable=False, server_default=text("('Titel')"))

    Created_By_Gebruiker = relationship('Gebruikers', primaryjoin='Beleidsrelaties.Created_By == Gebruikers.UUID')
    Modified_By_Gebruiker = relationship('Gebruikers', primaryjoin='Beleidsrelaties.Modified_By == Gebruikers.UUID')
    
    Ref_Van_Beleidskeuze = relationship('Beleidskeuzes', primaryjoin='Beleidsrelaties.Van_Beleidskeuze == Beleidskeuzes.UUID')
    Ref_Naar_Beleidskeuze = relationship('Beleidskeuzes', primaryjoin='Beleidsrelaties.Naar_Beleidskeuze == Beleidskeuzes.UUID')


class Beleidsrelaties_Schema(Base_Schema):
    Van_Beleidskeuze = MM.fields.UUID(
        required=True,
        allow_none=False,
        validate=[
            MM.validate.NoneOf(
                [
                    null_uuid,
                ]
            )
        ],
        obprops=["short"],
    )
    Naar_Beleidskeuze = MM.fields.UUID(
        required=True,
        allow_none=False,
        validate=[
            MM.validate.NoneOf(
                [
                    null_uuid,
                ]
            )
        ],
        obprops=["short"],
    )
    Omschrijving = MM.fields.Str(
        missing=None, validate=[HTML_Validate], obprops=["search_field", "short"]
    )
    Status = MM.fields.Str(
        required=True,
        validate=[MM.validate.OneOf(["Open", "Akkoord", "NietAkkoord", "Verbroken"])],
        obprops=["short"],
    )
    Aanvraag_Datum = MM.fields.DateTime(format="iso", required=True, obprops=["short"])
    Datum_Akkoord = MM.fields.DateTime(
        format="iso", allow_none=True, missing=None, obprops=["short"]
    )

    class Meta(Base_Schema.Meta):
        slug = "beleidsrelaties"
        table = "Beleidsrelaties"
        read_only = True
        ordered = True
        searchable = False
        references = {
            "Van_Beleidskeuze": UUID_Reference("Beleidskeuzes", Beleidskeuzes_Schema),
            "Naar_Beleidskeuze": UUID_Reference("Beleidskeuzes", Beleidskeuzes_Schema),
        }
