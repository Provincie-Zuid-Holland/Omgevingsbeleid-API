# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM

from Endpoints.endpoint import Base_Schema
from Endpoints.references import UUID_Reference, UUID_List_Reference, UUID_Linker_Schema

from globals import default_user_uuid

from Models.gebruikers import Gebruikers_Schema
from Models.ambities import Ambities_Schema



class Beleidskeuzes_Schema(Base_Schema):
    Eigenaar_1 = MM.fields.UUID(
        default=default_user_uuid, missing=default_user_uuid, allow_none=True, userfield=True, obprops=[])
    Eigenaar_2 = MM.fields.UUID(
        default=default_user_uuid, missing=default_user_uuid, allow_none=True, userfield=True, obprops=[])
    Portefeuillehouder_1 = MM.fields.UUID(
        default=default_user_uuid, missing=default_user_uuid, allow_none=True, obprops=[])
    Portefeuillehouder_2 = MM.fields.UUID(
        default=default_user_uuid, missing=default_user_uuid, allow_none=True, obprops=[])
    Opdrachtgever = MM.fields.UUID(
        default=default_user_uuid, missing=default_user_uuid, allow_none=True, obprops=[])
    Status = MM.fields.Str(required=True, validate=MM.validate.OneOf([
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
        "Vigerend gearchiveerd"]),
        obprops=[])
    Titel = MM.fields.Str(required=True, obprops=['search_field'])
    Omschrijving_Keuze = MM.fields.Str(missing=None, obprops=['search_field'])
    Omschrijving_Werking = MM.fields.Str(
        missing=None, obprops=['search_field'])
    Aanleiding = MM.fields.Str(missing=None, obprops=['search_field'])
    Afweging = MM.fields.Str(missing=None, obprops=['search_field'])
    Provinciaal_Belang = MM.fields.Str(missing=None, obprops=['search_field'])
    Weblink = MM.fields.Str(missing=None, obprops=[])
    Besluitnummer = MM.fields.Str(missing=None, obprops=[])
    Tags = MM.fields.Str(missing=None, obprops=[])
    Aanpassing_Op = MM.fields.UUID(
        missing=None, default=None, obprops=['excluded_post'])
    Ambities = MM.fields.Nested(UUID_Linker_Schema, many=True, default=[
    ], missing=[], obprops=['referencelist'])
  
    class Meta(Base_Schema.Meta):
        table = 'Beleidskeuzes'
        read_only = False
        ordered = True
        searchable = True
        references = {
            'Eigenaar_1': UUID_Reference('Gebruikers', Gebruikers_Schema),
            'Eigenaar_2': UUID_Reference('Gebruikers', Gebruikers_Schema),
            'Portefeuillehouder_1': UUID_Reference('Gebruikers', Gebruikers_Schema),
            'Portefeuillehouder_2': UUID_Reference('Gebruikers', Gebruikers_Schema),
            'Opdrachtgever': UUID_Reference('Gebruikers', Gebruikers_Schema),
            'Ambities': UUID_List_Reference('Beleidskeuze_Ambities', 'Ambities', 'Beleidskeuze_UUID', 'Ambitie_UUID', 'Koppeling_Omschrijving', Ambities_Schema)
        }
        status_conf = ('Status', 'Vigerend')
