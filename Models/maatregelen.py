# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from Endpoints.base_schema import Base_Schema
from Endpoints.references import (
    UUID_Reference,
    UUID_Linker_Schema,
    Reverse_UUID_Reference,
)
from Endpoints.validators import HTML_Validate
from Models.werkingsgebieden import Werkingsgebieden_Schema
from Models.short_schemas import Short_Beleidskeuze_Schema, Short_Beleidsmodule_Schema
from Models.gebruikers import Gebruikers_Schema
from Endpoints.status_data_manager import StatusDataManager

from globals import default_user_uuid

from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Integer, String, Unicode
from db import CommonMixin, db


class Beleidskeuze_Maatregelen_DB_Association(db.Model):
    __tablename__ = 'Beleidskeuze_Maatregelen'

    Beleidskeuze_UUID = Column('Beleidskeuze_UUID', ForeignKey('Beleidskeuzes.UUID'), primary_key=True)
    Maatregel_UUID = Column('Maatregel_UUID', ForeignKey('Maatregelen.UUID'), primary_key=True)
    Koppeling_Omschrijving = Column('Koppeling_Omschrijving', String(collation='SQL_Latin1_General_CP1_CI_AS'))

    Beleidskeuze = relationship("Beleidskeuzes", back_populates="Maatregelen")
    Maatregel = relationship("Maatregelen", back_populates="Beleidskeuzes")



class Beleidsmodule_Maatregelen_DB_Association(db.Model):
    __tablename__ = 'Beleidsmodule_Maatregelen'

    Beleidsmodule_UUID = Column('Beleidsmodule_UUID', ForeignKey('Beleidsmodules.UUID'), primary_key=True)
    Maatregel_UUID = Column('Maatregel_UUID', ForeignKey('Maatregelen.UUID'), primary_key=True)
    Koppeling_Omschrijving = Column('Koppeling_Omschrijving', String(collation='SQL_Latin1_General_CP1_CI_AS'))

    Beleidsmodule = relationship("Beleidsmodules", back_populates="Maatregelen")
    Maatregel = relationship("Maatregelen", back_populates="Beleidsmodules")


class Maatregelen_DB_Schema(CommonMixin, db.Model):
    __tablename__ = 'Maatregelen'

    Titel = Column(Unicode, nullable=False)
    Omschrijving = Column(Unicode)
    Toelichting = Column(Unicode)
    Toelichting_Raw = Column(Unicode)
    Weblink = Column(Unicode)
    Gebied = Column(ForeignKey('Werkingsgebieden.UUID'))
    Status = Column(Unicode(50))
    Gebied_Duiding = Column(Unicode)
    Tags = Column(Unicode)
    Aanpassing_Op = Column(ForeignKey('Maatregelen.UUID'))
    Eigenaar_1 = Column(ForeignKey('Gebruikers.UUID'))
    Eigenaar_2 = Column(ForeignKey('Gebruikers.UUID'))
    Portefeuillehouder_1 = Column(ForeignKey('Gebruikers.UUID'))
    Portefeuillehouder_2 = Column(ForeignKey('Gebruikers.UUID'))
    Opdrachtgever = Column(ForeignKey('Gebruikers.UUID'))

    Created_By_Gebruiker = relationship('Gebruikers', primaryjoin='Maatregelen.Created_By == Gebruikers.UUID')
    Modified_By_Gebruiker = relationship('Gebruikers', primaryjoin='Maatregelen.Modified_By == Gebruikers.UUID')
    
    Ref_Beleidskeuzes = relationship("Beleidskeuze_Maatregelen", back_populates="Maatregel")
            
    Ref_Eigenaar_1 = relationship('Gebruikers', primaryjoin='Maatregelen.Eigenaar_1 == Gebruikers.UUID')
    Ref_Eigenaar_2 = relationship('Gebruikers', primaryjoin='Maatregelen.Eigenaar_2 == Gebruikers.UUID')
    Ref_Portefeuillehouder_1 = relationship('Gebruikers', primaryjoin='Maatregelen.Portefeuillehouder_1 == Gebruikers.UUID')
    Ref_Portefeuillehouder_2 = relationship('Gebruikers', primaryjoin='Maatregelen.Portefeuillehouder_2 == Gebruikers.UUID')
    Ref_Opdrachtgever = relationship('Gebruikers', primaryjoin='Maatregelen.Opdrachtgever == Gebruikers.UUID')
    Ref_Gebied = relationship('Werkingsgebieden', primaryjoin='Maatregelen.Gebied == Werkingsgebieden.UUID')
    Ref_Beleidsmodules = relationship("Beleidsmodule_Maatregelen", back_populates="Maatregel")

status_options = [
    "Definitief ontwerp GS",
    "Definitief ontwerp GS concept",
    "Definitief ontwerp PS",
    "Niet-Actief",
    "Ontwerp GS",
    "Ontwerp GS Concept",
    "Ontwerp in inspraak",
    "Ontwerp PS",
    "Uitgecheckt",
    "Vastgesteld",
    "Vigerend",
    "Vigerend gearchiveerd",
]


class Maatregelen_Schema(Base_Schema):
    Eigenaar_1 = MM.fields.UUID(
        missing=default_user_uuid,
        allow_none=True,
        userfield=True,
        obprops=[],
    )
    Eigenaar_2 = MM.fields.UUID(
        missing=default_user_uuid,
        allow_none=True,
        userfield=True,
        obprops=[],
    )
    Portefeuillehouder_1 = MM.fields.UUID(
        missing=default_user_uuid,
        allow_none=True,
        obprops=[],
    )
    Portefeuillehouder_2 = MM.fields.UUID(
        missing=default_user_uuid,
        allow_none=True,
        obprops=[],
    )
    Opdrachtgever = MM.fields.UUID(
        missing=default_user_uuid,
        allow_none=True,
        obprops=[],
    )
    Titel = MM.fields.Str(
        required=True, validate=[HTML_Validate], obprops=["search_title", "short"]
    )
    Omschrijving = MM.fields.Str(
        missing=None, validate=[HTML_Validate], obprops=[]
    )
    Toelichting = MM.fields.Str(missing=None, validate=[HTML_Validate], obprops=["search_description"])
    Toelichting_Raw = MM.fields.Str(missing=None, obprops=[])
    Status = MM.fields.Str(
        missing=None, validate=[MM.validate.OneOf(status_options)], obprops=["short"]
    )
    Weblink = MM.fields.Str(missing=None, obprops=[])
    Gebied = MM.fields.UUID(missing=None, obprops=[])
    Gebied_Duiding = MM.fields.Str(
        allow_none=True,
        missing="Indicatief",
        validate=[MM.validate.OneOf(["Indicatief", "Exact"])],
        obprops=[],
    )
    Tags = MM.fields.Str(missing=None, obprops=[])
    Aanpassing_Op = MM.fields.UUID(
        missing=None, obprops=["excluded_post", "not_inherited"]
    )
    Ref_Beleidskeuzes = MM.fields.Nested(
        UUID_Linker_Schema,
        many=True,
        obprops=["referencelist", "excluded_patch", "excluded_post"],
    )
    Ref_Beleidsmodules = MM.fields.Nested(
        UUID_Linker_Schema,
        many=True,
        obprops=["referencelist", "excluded_patch", "excluded_post"],
    )
    Latest_Version = MM.fields.UUID(
        required=False,
        missing=None,
        obprops=["excluded_post", "excluded_patch", "calculated"],
    )
    Latest_Status = MM.fields.Str(
        required=False,
        missing=None,
        obprops=["excluded_post", "excluded_patch", "calculated"],
        validate=[MM.validate.OneOf(status_options)],
    )
    Effective_Version = MM.fields.UUID(
        required=False,
        missing=None,
        obprops=["excluded_post", "excluded_patch", "calculated"],
    )

    class Meta(Base_Schema.Meta):
        slug = "maatregelen"
        table = "Maatregelen"
        read_only = False
        ordered = True
        searchable = True
        geo_searchable = "Gebied"
        status_conf = ("Status", "Vigerend")
        references = {
            "Ref_Beleidskeuzes": Reverse_UUID_Reference(
                "Beleidskeuze_Maatregelen",
                "Beleidskeuzes",
                "Maatregel_UUID",
                "Beleidskeuze_UUID",
                "Koppeling_Omschrijving",
                Short_Beleidskeuze_Schema,
            ),
            "Eigenaar_1": UUID_Reference("Gebruikers", Gebruikers_Schema),
            "Eigenaar_2": UUID_Reference("Gebruikers", Gebruikers_Schema),
            "Portefeuillehouder_1": UUID_Reference("Gebruikers", Gebruikers_Schema),
            "Portefeuillehouder_2": UUID_Reference("Gebruikers", Gebruikers_Schema),
            "Opdrachtgever": UUID_Reference("Gebruikers", Gebruikers_Schema),
            "Gebied": UUID_Reference("Werkingsgebieden", Werkingsgebieden_Schema),
            "Ref_Beleidsmodules": Reverse_UUID_Reference(
                "Beleidsmodule_Maatregelen",
                "Beleidsmodules",
                "Maatregel_UUID",
                "Beleidsmodule_UUID",
                "Koppeling_Omschrijving",
                Short_Beleidsmodule_Schema,
            ),
        }
        graph_conf = "Titel"
        manager = StatusDataManager
