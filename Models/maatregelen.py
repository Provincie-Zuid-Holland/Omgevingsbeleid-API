# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from Endpoints.base_schema import Base_Schema
from Endpoints.references import UUID_Reference, UUID_Linker_Schema, Reverse_UUID_Reference
from Endpoints.validators import HTML_Validate
from Models.werkingsgebieden import Werkingsgebieden_Schema
from Models.short_schemas import Short_Beleidskeuze_Schema, Short_Beleidsmodule_Schema
from Models.gebruikers import Gebruikers_Schema


from globals import default_user_uuid


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
        "Vigerend gearchiveerd"]

class Maatregelen_Schema(Base_Schema):
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
    Titel = MM.fields.Str(required=True, validate=[
                          HTML_Validate], obprops=['search_title', 'short'])
    Omschrijving = MM.fields.Str(missing=None, validate=[
                                 HTML_Validate], obprops=['search_description'])
    Toelichting = MM.fields.Str(missing=None, validate=[
                                HTML_Validate], obprops=[])
    Toelichting_Raw = MM.fields.Str(missing=None, obprops=[])
    Status = MM.fields.Str(missing=None, validate=[MM.validate.OneOf(status_options)],
        obprops=['short'])
    Weblink = MM.fields.Str(missing=None, obprops=[])
    Gebied = MM.fields.UUID(missing=None, obprops=[])
    Gebied_Duiding = MM.fields.Str(allow_none=True, missing="Indicatief",
                                   validate=[MM.validate.OneOf(["Indicatief", "Exact"])], obprops=[])
    Tags = MM.fields.Str(missing=None, obprops=[])
    Aanpassing_Op = MM.fields.UUID(
        missing=None, default=None, obprops=['excluded_post', 'not_inherited'])
    Ref_Beleidskeuzes = MM.fields.Nested(
        UUID_Linker_Schema, many=True, obprops=['referencelist', 'excluded_patch', 'excluded_post'])
    Ref_Beleidsmodules = MM.fields.Nested(
        UUID_Linker_Schema, many=True, obprops=['referencelist', 'excluded_patch', 'excluded_post'])
    # Latest_Version = MM.fields.UUID(required=False, missing=None, obprops=['excluded_post', 'excluded_patch'])
    # Latest_Status = MM.fields.Str(required=False, missing=None, obprops=['excluded_post', 'excluded_patch'], validate=[MM.validate.OneOf(status_options)])
    # Effective_Version = MM.fields.UUID(required=False, missing=None, obprops=['excluded_post', 'excluded_patch'])

    class Meta(Base_Schema.Meta):
        slug = 'maatregelen'
        table = 'Maatregelen'
        read_only = False
        ordered = True
        searchable = True
        geo_searchable = 'Gebied'
        status_conf = ('Status', 'Vigerend')
        references = {
            'Ref_Beleidskeuzes': Reverse_UUID_Reference('Beleidskeuze_Maatregelen',
                                                    'Beleidskeuzes',
                                                    'Maatregel_UUID',
                                                    'Beleidskeuze_UUID',
                                                    'Koppeling_Omschrijving',
                                                    Short_Beleidskeuze_Schema
                                                    ),
            'Eigenaar_1': UUID_Reference('Gebruikers', Gebruikers_Schema),
            'Eigenaar_2': UUID_Reference('Gebruikers', Gebruikers_Schema),
            'Portefeuillehouder_1': UUID_Reference('Gebruikers', Gebruikers_Schema),
            'Portefeuillehouder_2': UUID_Reference('Gebruikers', Gebruikers_Schema),
            'Opdrachtgever': UUID_Reference('Gebruikers', Gebruikers_Schema),
            'Gebied': UUID_Reference('Werkingsgebieden', Werkingsgebieden_Schema),
            'Ref_Beleidsmodules': Reverse_UUID_Reference('Beleidsmodule_Maatregelen', 'Beleidsmodules', 'Maatregel_UUID', 'Beleidsmodule_UUID', 'Koppeling_Omschrijving', Short_Beleidsmodule_Schema)}
        graph_conf = 'Titel'