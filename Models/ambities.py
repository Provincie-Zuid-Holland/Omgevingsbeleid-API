# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from Endpoints.base_schema import Base_Schema
from Endpoints.references import (Reverse_ID_Reference, Reverse_UUID_Reference,
                                  UUID_Linker_Schema)
from Endpoints.validators import HTML_Validate
from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy_utils import generic_repr

from db import CommonMixin, Base, db
from Models.short_schemas import Short_Beleidskeuze_Schema

@generic_repr
class Ambities_DB_Schema(CommonMixin, db.Model):
    __tablename__ = 'Ambities'

    Titel = Column(String)
    Omschrijving = Column(String)
    Weblink = Column(String)


class Ambities_Schema(Base_Schema):
    Titel = MM.fields.Str(
        required=True, validate=[HTML_Validate], obprops=["search_title", "short"]
    )
    Omschrijving = MM.fields.Str(
        missing=None,
        validate=[HTML_Validate],
        obprops=["search_description", "large_data"],
    )
    Weblink = MM.fields.Str(missing=None, obprops=[])
    Ref_Beleidskeuzes = MM.fields.Nested(
        UUID_Linker_Schema,
        many=True,
        obprops=["referencelist", "excluded_patch", "excluded_post"],
    )

    class Meta(Base_Schema.Meta):
        slug = "ambities"
        table = "Ambities"
        read_only = False
        ordered = True
        searchable = True
        references = {
            "Ref_Beleidskeuzes": Reverse_UUID_Reference(
                "Beleidskeuze_Ambities",
                "Beleidskeuzes",
                "Ambitie_UUID",
                "Beleidskeuze_UUID",
                "Koppeling_Omschrijving",
                Short_Beleidskeuze_Schema,
            )
        }
        graph_conf = "Titel"
