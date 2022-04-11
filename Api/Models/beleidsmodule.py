# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Integer, String, Unicode, DateTime

from Api.Endpoints.base_schema import Base_Schema
from Api.Endpoints.references import (
    UUID_Reference,
    UUID_List_Reference,
    UUID_Linker_Schema,
)
from Api.Endpoints.validators import HTML_Validate
from Api.settings import default_user_uuid, min_datetime
import Api.Models.maatregelen
import Api.Models.beleidskeuzes
from Api.database import CommonMixin, db


class Beleidsmodules(CommonMixin, db.Model):
    __tablename__ = "Beleidsmodules"

    Titel = Column(Unicode(150), nullable=False)
    Besluit_Datum = Column(DateTime)

    Created_By_Gebruiker = relationship(
        "Gebruikers", primaryjoin="Beleidsmodules.Created_By == Gebruikers.UUID"
    )
    Modified_By_Gebruiker = relationship(
        "Gebruikers", primaryjoin="Beleidsmodules.Modified_By == Gebruikers.UUID"
    )

    Maatregelen = relationship(
        "Beleidsmodule_Maatregelen", back_populates="Beleidsmodule"
    )
    Beleidskeuzes = relationship(
        "Beleidsmodule_Beleidskeuzes", back_populates="Beleidsmodule"
    )


class Beleidsmodule_Schema(Base_Schema):
    Titel = MM.fields.Str(required=True, obprops=["short"])
    Besluit_Datum = MM.fields.DateTime(
        format="iso", missing=min_datetime, allow_none=True, obprops=[]
    )
    Maatregelen = MM.fields.Nested(
        UUID_Linker_Schema, many=True, obprops=["referencelist", "short"]
    )
    Beleidskeuzes = MM.fields.Nested(
        UUID_Linker_Schema, many=True, obprops=["referencelist", "short"]
    )

    class Meta(Base_Schema.Meta):
        slug = "beleidsmodules"
        table = "Beleidsmodules"
        read_only = False
        ordered = True
        searchable = False
        references = {
            "Maatregelen": UUID_List_Reference(
                "Beleidsmodule_Maatregelen",
                "Maatregelen",
                "Beleidsmodule_UUID",
                "Maatregel_UUID",
                "Koppeling_Omschrijving",
                Api.Models.maatregelen.Maatregelen_Schema,
            ),
            "Beleidskeuzes": UUID_List_Reference(
                "Beleidsmodule_Beleidskeuzes",
                "Beleidskeuzes",
                "Beleidsmodule_UUID",
                "Beleidskeuze_UUID",
                "Koppeling_Omschrijving",
                Api.Models.beleidskeuzes.Beleidskeuzes_Schema,
            ),
        }
