# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM

# from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
# from sqlalchemy.orm import declarative_base   s

from Endpoints.base_schema import Base_Schema
from Endpoints.references import (
    UUID_Linker_Schema,
    Reverse_UUID_Reference,
    Reverse_ID_Reference,
)
from Endpoints.validators import HTML_Validate
from Models.short_schemas import Short_Beleidskeuze_Schema
from Models.db import db

class Base_DB_Schema():
    ID = db.Column(db.Integer)
    UUID = db.Column(db.String(255), primary_key=True) # @todo: UUID
    Begin_Geldigheid = db.Column(db.DateTime)  
    Eind_Geldigheid = db.Column(db.DateTime)  
    Created_By = db.Column(db.String(255)) # @todo: UUID
    Created_Date = db.Column(db.DateTime)  
    Modified_By = db.Column(db.String(255)) # @todo: UUID
    Modified_Date = db.Column(db.DateTime)
    

# an example mapping using the base
class Ambities_DB_Schema(Base_DB_Schema, db.Model):
    __tablename__ = 'Ambities'

    Titel = db.Column(db.String(255))
    Omschrijving = db.Column(db.String(255))
    Weblink = db.Column(db.String(255))
    Jordy = db.Column(db.Integer)
    

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
