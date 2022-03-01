# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2022 Provincie Zuid-Holland

import marshmallow as MM
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Integer, String, Unicode

from Api.Endpoints.base_schema import Base_Schema
from Api.Endpoints.references import (
    UUID_Reference,
    UUID_List_Reference,
    UUID_Linker_Schema,
    Reverse_UUID_Reference,
)
from Api.Endpoints.validators import HTML_Validate
from Api.settings import default_user_uuid
import Api.Models.gebruikers
import Api.Models.ambities
import Api.Models.belangen
import Api.Models.werkingsgebieden
import Api.Models.themas
import Api.Models.beleidsdoelen
import Api.Models.beleidsprestaties
import Api.Models.beleidsregels
import Api.Models.maatregelen
import Api.Models.verordeningen
from Api.Models.short_schemas import Short_Beleidsmodule_Schema, Short_Beleidskeuze_Schema
from Api.Endpoints.status_data_manager import StatusDataManager
from Api.database import CommonMixin, db


class Beleidsmodule_Beleidskeuzes(db.Model):
    __tablename__ = 'Beleidsmodule_Beleidskeuzes'

    Beleidsmodule_UUID = Column('Beleidsmodule_UUID', ForeignKey('Beleidsmodules.UUID'), primary_key=True)
    Beleidskeuze_UUID = Column('Beleidskeuze_UUID', ForeignKey('Beleidskeuzes.UUID'), primary_key=True)
    Koppeling_Omschrijving = Column('Koppeling_Omschrijving', String(collation='SQL_Latin1_General_CP1_CI_AS'))

    Beleidsmodule = relationship("Beleidsmodules", back_populates="Beleidskeuzes")
    Beleidskeuze = relationship("Beleidskeuzes", back_populates="Beleidsmodules")


class Beleidskeuzes(CommonMixin, db.Model):
    __tablename__ = 'Beleidskeuzes'

    Eigenaar_1 = Column(ForeignKey('Gebruikers.UUID'))
    Eigenaar_2 = Column(ForeignKey('Gebruikers.UUID'))
    Portefeuillehouder_1 = Column(ForeignKey('Gebruikers.UUID'))
    Portefeuillehouder_2 = Column(ForeignKey('Gebruikers.UUID'))
    Opdrachtgever = Column(ForeignKey('Gebruikers.UUID'))
    Titel = Column(Unicode, nullable=False)
    Omschrijving_Keuze = Column(Unicode)
    Omschrijving_Werking = Column(Unicode)
    Provinciaal_Belang = Column(Unicode)
    Aanleiding = Column(Unicode)
    Afweging = Column(Unicode)
    Besluitnummer = Column(Unicode)
    Tags = Column(Unicode)
    Aanpassing_Op = Column(ForeignKey('Beleidskeuzes.UUID'))
    Status = Column(Unicode(50), nullable=False)
    Weblink = Column(Unicode(200))

    Created_By_Gebruiker = relationship('Gebruikers', primaryjoin='Beleidskeuzes.Created_By == Gebruikers.UUID')
    Modified_By_Gebruiker = relationship('Gebruikers', primaryjoin='Beleidskeuzes.Modified_By == Gebruikers.UUID')
    
    Ref_Eigenaar_1 = relationship('Gebruikers', primaryjoin='Beleidskeuzes.Eigenaar_1 == Gebruikers.UUID')
    Ref_Eigenaar_2 = relationship('Gebruikers', primaryjoin='Beleidskeuzes.Eigenaar_2 == Gebruikers.UUID')
    Ref_Portefeuillehouder_1 = relationship('Gebruikers', primaryjoin='Beleidskeuzes.Portefeuillehouder_1 == Gebruikers.UUID')
    Ref_Portefeuillehouder_2 = relationship('Gebruikers', primaryjoin='Beleidskeuzes.Portefeuillehouder_2 == Gebruikers.UUID')
    Ref_Opdrachtgever = relationship('Gebruikers', primaryjoin='Beleidskeuzes.Opdrachtgever == Gebruikers.UUID')
    Ambities = relationship("Beleidskeuze_Ambities", back_populates="Beleidskeuze")
    Belangen = relationship("Beleidskeuze_Belangen", back_populates="Beleidskeuze")
    Beleidsdoelen = relationship("Beleidskeuze_Beleidsdoelen", back_populates="Beleidskeuze")
    Beleidsprestaties = relationship("Beleidskeuze_Beleidsprestaties", back_populates="Beleidskeuze")
    Beleidsregels = relationship("Beleidskeuze_Beleidsregels", back_populates="Beleidskeuze")
    Maatregelen = relationship("Beleidskeuze_Maatregelen", back_populates="Beleidskeuze")
    Themas = relationship("Beleidskeuze_Themas", back_populates="Beleidskeuze")
    Verordeningen = relationship("Beleidskeuze_Verordeningen", back_populates="Beleidskeuze")
    Werkingsgebieden = relationship("Beleidskeuze_Werkingsgebieden", back_populates="Beleidskeuze")
    # Beleidsrelaties = relationship("Beleidsrelaties", back_populates="Beleidskeuzes")
    Beleidsmodules = relationship("Beleidsmodule_Beleidskeuzes", back_populates="Beleidskeuze")
            

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


class Beleidskeuzes_Schema(Base_Schema):
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
    Status = MM.fields.Str(
        required=True, validate=[MM.validate.OneOf(status_options)], obprops=["short"]
    )
    Titel = MM.fields.Str(required=True, obprops=["search_title", "short"])
    Omschrijving_Keuze = MM.fields.Str(
        missing=None, validate=[HTML_Validate], obprops=["search_description"]
    )
    Omschrijving_Werking = MM.fields.Str(
        missing=None, validate=[HTML_Validate], obprops=["search_description"]
    )
    Aanleiding = MM.fields.Str(missing=None, validate=[HTML_Validate], obprops=[])
    Afweging = MM.fields.Str(missing=None, validate=[HTML_Validate], obprops=[])
    Provinciaal_Belang = MM.fields.Str(
        missing=None, validate=[HTML_Validate], obprops=[]
    )
    Weblink = MM.fields.Str(missing=None, validate=[HTML_Validate], obprops=[])
    Besluitnummer = MM.fields.Str(missing=None, obprops=[])
    Tags = MM.fields.Str(missing=None, obprops=[])
    Aanpassing_Op = MM.fields.UUID(
        missing=None, obprops=["excluded_post", "not_inherited"]
    )
    Ambities = MM.fields.Nested(
        UUID_Linker_Schema, many=True, obprops=["referencelist"]
    )
    Belangen = MM.fields.Nested(
        UUID_Linker_Schema, many=True, obprops=["referencelist"]
    )
    Beleidsdoelen = MM.fields.Nested(
        UUID_Linker_Schema, many=True, obprops=["referencelist"]
    )
    Beleidsprestaties = MM.fields.Nested(
        UUID_Linker_Schema, many=True, obprops=["referencelist"]
    )
    Beleidsregels = MM.fields.Nested(
        UUID_Linker_Schema, many=True, obprops=["referencelist"]
    )
    Maatregelen = MM.fields.Nested(
        UUID_Linker_Schema, many=True, obprops=["referencelist"]
    )
    Themas = MM.fields.Nested(UUID_Linker_Schema, many=True, obprops=["referencelist"])
    Verordeningen = MM.fields.Nested(
        UUID_Linker_Schema, many=True, obprops=["referencelist"]
    )
    Werkingsgebieden = MM.fields.Nested(
        UUID_Linker_Schema, many=True, obprops=["referencelist"]
    )
    Ref_Beleidsmodules = MM.fields.Nested(
        UUID_Linker_Schema,
        many=True,
        obprops=["referencelist", "excluded_patch", "excluded_post", "short"],
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
        slug = "beleidskeuzes"
        table = "Beleidskeuzes"
        read_only = False
        ordered = True
        searchable = True
        geo_searchable = "Werkingsgebieden"
        references = {
            "Eigenaar_1": UUID_Reference(
                "Gebruikers", Api.Models.gebruikers.Gebruikers_Schema
            ),
            "Eigenaar_2": UUID_Reference(
                "Gebruikers", Api.Models.gebruikers.Gebruikers_Schema
            ),
            "Portefeuillehouder_1": UUID_Reference(
                "Gebruikers", Api.Models.gebruikers.Gebruikers_Schema
            ),
            "Portefeuillehouder_2": UUID_Reference(
                "Gebruikers", Api.Models.gebruikers.Gebruikers_Schema
            ),
            "Opdrachtgever": UUID_Reference(
                "Gebruikers", Api.Models.gebruikers.Gebruikers_Schema
            ),
            "Ambities": UUID_List_Reference(
                "Beleidskeuze_Ambities",
                "Ambities",
                "Beleidskeuze_UUID",
                "Ambitie_UUID",
                "Koppeling_Omschrijving",
                Api.Models.ambities.Ambities_Schema,
            ),
            "Belangen": UUID_List_Reference(
                "Beleidskeuze_Belangen",
                "Belangen",
                "Beleidskeuze_UUID",
                "Belang_UUID",
                "Koppeling_Omschrijving",
                Api.Models.belangen.Belangen_Schema,
            ),
            "Beleidsdoelen": UUID_List_Reference(
                "Beleidskeuze_Beleidsdoelen",
                "Beleidsdoelen",
                "Beleidskeuze_UUID",
                "Beleidsdoel_UUID",
                "Koppeling_Omschrijving",
                Api.Models.beleidsdoelen.Beleidsdoelen_Schema,
            ),
            "Beleidsprestaties": UUID_List_Reference(
                "Beleidskeuze_Beleidsprestaties",
                "Beleidsprestaties",
                "Beleidskeuze_UUID",
                "Beleidsprestatie_UUID",
                "Koppeling_Omschrijving",
                Api.Models.beleidsprestaties.Beleidsprestaties_Schema,
            ),
            "Beleidsregels": UUID_List_Reference(
                "Beleidskeuze_Beleidsregels",
                "Beleidsregels",
                "Beleidskeuze_UUID",
                "Beleidsregel_UUID",
                "Koppeling_Omschrijving",
                Api.Models.beleidsregels.Beleidsregels_Schema,
            ),
            "Maatregelen": UUID_List_Reference(
                "Beleidskeuze_Maatregelen",
                "Maatregelen",
                "Beleidskeuze_UUID",
                "Maatregel_UUID",
                "Koppeling_Omschrijving",
                Api.Models.maatregelen.Maatregelen_Schema,
            ),
            "Themas": UUID_List_Reference(
                "Beleidskeuze_Themas",
                "Themas",
                "Beleidskeuze_UUID",
                "Thema_UUID",
                "Koppeling_Omschrijving",
                Api.Models.themas.Themas_Schema,
            ),
            "Verordeningen": UUID_List_Reference(
                "Beleidskeuze_Verordeningen",
                "Verordeningen",
                "Beleidskeuze_UUID",
                "Verordening_UUID",
                "Koppeling_Omschrijving",
                Api.Models.verordeningen.Verordeningen_Schema,
            ),
            "Werkingsgebieden": UUID_List_Reference(
                "Beleidskeuze_Werkingsgebieden",
                "Werkingsgebieden",
                "Beleidskeuze_UUID",
                "Werkingsgebied_UUID",
                "Koppeling_Omschrijving",
                Api.Models.werkingsgebieden.Werkingsgebieden_Schema,
            ),
            "Ref_Beleidsmodules": Reverse_UUID_Reference(
                "Beleidsmodule_Beleidskeuzes",
                "Beleidsmodules",
                "Beleidskeuze_UUID",
                "Beleidsmodule_UUID",
                "Koppeling_Omschrijving",
                Short_Beleidsmodule_Schema,
            ),
        }
        status_conf = ("Status", "Vigerend")
        graph_conf = "Titel"
        manager = StatusDataManager
