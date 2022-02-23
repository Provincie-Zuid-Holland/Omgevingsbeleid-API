# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Integer, String, Unicode, DateTime, text, Sequence

from Api.Endpoints.base_schema import Base_Schema
from Api.Endpoints.references import UUID_Reference
from Api.Endpoints.validators import HTML_Validate
from Api.Models.beleidskeuzes import Beleidskeuzes_Schema
from Api.settings import null_uuid
from Api.database import db


class Beleidsrelaties(db.Model):
    __tablename__ = 'Beleidsrelaties'

    # Overwrites because of different nullable value
    # @todo: should probably be alligned with CommonMixin at some point
    @declared_attr
    def ID(cls):
        seq_name = 'seq_{name}'.format(name=cls.__name__)
        seq = Sequence(seq_name)
        return Column(Integer, seq, nullable=False, server_default=seq.next_value())

    UUID = Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("(newid())"))

    Begin_Geldigheid = Column(DateTime, nullable=True)
    Eind_Geldigheid = Column(DateTime, nullable=True)
    Created_Date = Column(DateTime, nullable=True)
    Modified_Date = Column(DateTime, nullable=True)

    @declared_attr
    def Created_By(cls):
        return Column('Created_By', ForeignKey('Gebruikers.UUID'), nullable=True)

    @declared_attr
    def Modified_By(cls):
        return Column('Modified_By', ForeignKey('Gebruikers.UUID'), nullable=True)

    # The rest of the model as normal
    Omschrijving = Column(Unicode)
    Status = Column(Unicode(50))
    Aanvraag_Datum = Column(DateTime)
    Datum_Akkoord = Column(DateTime)
    Titel = Column(Unicode(50), nullable=False, server_default=text("('Titel')"))

    Van_Beleidskeuze = Column(ForeignKey('Beleidskeuzes.UUID'), nullable=False)
    Naar_Beleidskeuze = Column(ForeignKey('Beleidskeuzes.UUID'), nullable=False)

    Ref_Van_Beleidskeuze = relationship('Beleidskeuzes', primaryjoin='Beleidsrelaties.Van_Beleidskeuze == Beleidskeuzes.UUID')
    Ref_Naar_Beleidskeuze = relationship('Beleidskeuzes', primaryjoin='Beleidsrelaties.Naar_Beleidskeuze == Beleidskeuzes.UUID')

    Created_By_Gebruiker = relationship('Gebruikers', primaryjoin='Beleidsrelaties.Created_By == Gebruikers.UUID')
    Modified_By_Gebruiker = relationship('Gebruikers', primaryjoin='Beleidsrelaties.Modified_By == Gebruikers.UUID')


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
        read_only = False
        ordered = True
        searchable = False
        manager = RelationDataManager
        references = {
            "Van_Beleidskeuze": UUID_Reference("Beleidskeuzes", Beleidskeuzes_Schema),
            "Naar_Beleidskeuze": UUID_Reference("Beleidskeuzes", Beleidskeuzes_Schema),
        }
