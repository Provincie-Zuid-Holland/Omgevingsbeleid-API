# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from Endpoints.normal import Normal_Schema
from globals import default_user_uuid


class Beleidskeuze_Schema(Normal_Schema):
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

    class Meta(Normal_Schema.Meta):
        table = 'Beleidskeuzes'
        read_only = False
        ordered = True
        searchable = True

    # WerkingsGebieden = MM.fields.Nested(
    #     Link_Schema, many=True, default=[], missing=[], obprops=['linker', 'geo_field'])
    # BeleidsRegels = MM.fields.Nested(
    #     Link_Schema, many=True,  default=[], missing=[], obprops=['linker'])
    # Verordening = MM.fields.Nested(
    #     Link_Schema, many=True,  default=[], missing=[], obprops=['linker'])
    # Maatregelen = MM.fields.Nested(
    #     Link_Schema, many=True,  default=[], missing=[], obprops=['linker'])
    # Themas = MM.fields.Nested(Link_Schema, many=True, default=[], missing=[], obprops=['linker'])
    # Ambities = MM.fields.Nested(Link_Schema, many=True, default=[], missing=[], obprops=['linker'])
    # Doelen = MM.fields.Nested(Link_Schema, many=True, default=[], missing=[], obprops=['linker'])
    # Belangen = MM.fields.Nested(
    #     Link_Schema, many=True, default=[], missing=[], obprops=['linker'])
    # Opgaven = MM.fields.Nested(Link_Schema, many=True, default=[], missing=[], obprops=['linker'])
