# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Integer, String, Unicode

from Api.Endpoints.base_schema import Base_Schema
from Api.Endpoints.references import (
    UUID_Reference,
    UUID_Linker_Schema,
    Reverse_UUID_Reference,
)
from Api.Models.gebruikers import Gebruikers_Schema
from Api.Models.werkingsgebieden import Werkingsgebieden_Schema
from Api.Models.short_schemas import Short_Beleidskeuze_Schema
from Api.settings import default_user_uuid
from Api.database import CommonMixin, db


class Beleidskeuze_Verordeningen(db.Model):
    __tablename__ = 'Beleidskeuze_Verordeningen'

    Beleidskeuze_UUID = Column('Beleidskeuze_UUID', ForeignKey('Beleidskeuzes.UUID'), primary_key=True)
    Verordening_UUID = Column('Verordening_UUID', ForeignKey('Verordeningen.UUID'), primary_key=True)
    Koppeling_Omschrijving = Column('Koppeling_Omschrijving', String(collation='SQL_Latin1_General_CP1_CI_AS'))

    Beleidskeuze = relationship("Beleidskeuzes", back_populates="Verordeningen")
    Verordening = relationship("Verordeningen", back_populates="Beleidskeuzes")


class Verordeningen(CommonMixin, db.Model):
    __tablename__ = 'Verordeningen'

    Portefeuillehouder_1 = Column(ForeignKey('Gebruikers.UUID'))
    Portefeuillehouder_2 = Column(ForeignKey('Gebruikers.UUID'))
    Eigenaar_1 = Column(ForeignKey('Gebruikers.UUID'))
    Eigenaar_2 = Column(ForeignKey('Gebruikers.UUID'))
    Opdrachtgever = Column(ForeignKey('Gebruikers.UUID'))
    Titel = Column(Unicode)
    Inhoud = Column(Unicode)
    Weblink = Column(Unicode)
    Status = Column(Unicode(50), nullable=False)
    Type = Column(Unicode, nullable=False)
    Gebied = Column(ForeignKey('Werkingsgebieden.UUID'))
    Volgnummer = Column(Unicode, nullable=False)

    Created_By_Gebruiker = relationship('Gebruikers', primaryjoin='Verordeningen.Created_By == Gebruikers.UUID')
    Modified_By_Gebruiker = relationship('Gebruikers', primaryjoin='Verordeningen.Modified_By == Gebruikers.UUID')
    
    Ref_Eigenaar_1 = relationship('Gebruikers', primaryjoin='Verordeningen.Eigenaar_1 == Gebruikers.UUID')
    Ref_Eigenaar_2 = relationship('Gebruikers', primaryjoin='Verordeningen.Eigenaar_2 == Gebruikers.UUID')
    Ref_Portefeuillehouder_1 = relationship('Gebruikers', primaryjoin='Verordeningen.Portefeuillehouder_1 == Gebruikers.UUID')
    Ref_Portefeuillehouder_2 = relationship('Gebruikers', primaryjoin='Verordeningen.Portefeuillehouder_2 == Gebruikers.UUID')
    Ref_Opdrachtgever = relationship('Gebruikers', primaryjoin='Verordeningen.Opdrachtgever == Gebruikers.UUID')
    Ref_Gebied = relationship('Werkingsgebieden', primaryjoin='Verordeningen.Gebied == Werkingsgebieden.UUID')
    Beleidskeuzes = relationship("Beleidskeuze_Verordeningen", back_populates="Verordening")


class Verordeningen_Schema(Base_Schema):
    Eigenaar_1 = MM.fields.UUID(
        default=default_user_uuid,
        missing=default_user_uuid,
        allow_none=True,
        userfield=True,
        obprops=[],
    )
    Eigenaar_2 = MM.fields.UUID(
        default=default_user_uuid,
        missing=default_user_uuid,
        allow_none=True,
        userfield=True,
        obprops=[],
    )
    Portefeuillehouder_1 = MM.fields.UUID(
        default=default_user_uuid,
        missing=default_user_uuid,
        allow_none=True,
        obprops=[],
    )
    Portefeuillehouder_2 = MM.fields.UUID(
        default=default_user_uuid,
        missing=default_user_uuid,
        allow_none=True,
        obprops=[],
    )
    Opdrachtgever = MM.fields.UUID(
        default=default_user_uuid,
        missing=default_user_uuid,
        allow_none=True,
        obprops=[],
    )
    Titel = MM.fields.Str(missing=None, obprops=["short", "search_title"])
    Inhoud = MM.fields.Str(missing=None, obprops=["search_description"])
    Weblink = MM.fields.Str(missing=None, obprops=[])
    Status = MM.fields.Str(missing=None, obprops=[])
    Volgnummer = MM.fields.Str(missing=None, obprops=["short"])
    Type = MM.fields.Str(
        missing=None,
        validate=[
            MM.validate.OneOf(["Hoofdstuk", "Afdeling", "Paragraaf", "Artikel", "Lid"])
        ],
        obprops=["short"],
    )
    Gebied = MM.fields.UUID(missing=None, obprops=[])
    Ref_Beleidskeuzes = MM.fields.Nested(
        UUID_Linker_Schema,
        many=True,
        obprops=["referencelist", "excluded_patch", "excluded_post"],
    )

    class Meta(Base_Schema.Meta):
        slug = "verordeningen"
        table = "Verordeningen"
        read_only = False
        ordered = True
        searchable = False
        geo_searchable = "Gebied"
        references = references = {
            "Eigenaar_1": UUID_Reference("Gebruikers", Gebruikers_Schema),
            "Eigenaar_2": UUID_Reference("Gebruikers", Gebruikers_Schema),
            "Portefeuillehouder_1": UUID_Reference("Gebruikers", Gebruikers_Schema),
            "Portefeuillehouder_2": UUID_Reference("Gebruikers", Gebruikers_Schema),
            "Opdrachtgever": UUID_Reference("Gebruikers", Gebruikers_Schema),
            "Gebied": UUID_Reference("Werkingsgebieden", Werkingsgebieden_Schema),
            "Ref_Beleidskeuzes": Reverse_UUID_Reference(
                "Beleidskeuze_Verordeningen",
                "Beleidskeuzes",
                "Verordening_UUID",
                "Beleidskeuze_UUID",
                "Koppeling_Omschrijving",
                Short_Beleidskeuze_Schema,
            ),
        }
        graph_conf = "Titel"
