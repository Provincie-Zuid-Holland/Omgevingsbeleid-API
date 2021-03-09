# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland
import marshmallow as MM
from Endpoints.endpoint import Base_Schema
from Endpoints.references import UUID_Reference, UUID_List_Reference, UUID_Linker_Schema
from globals import default_user_uuid, null_uuid

class Ambities_Schema(Base_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_title'])
    Omschrijving = MM.fields.Str(missing=None, obprops=['search_description'])
    Weblink = MM.fields.Str(missing=None, obprops=[])

    class Meta(Base_Schema.Meta):
        slug = 'ambities'
        table = 'Ambities'
        read_only = False
        ordered = True
        searchable = True


class Belangen_Schema(Base_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_title'])
    Omschrijving = MM.fields.Str(missing=None, obprops=['search_description'])
    Weblink = MM.fields.Str(missing=None, obprops=[])
    Type = MM.fields.Str(missing=None, validate=MM.validate.OneOf(
        ['Nationaal Belang', 'Wettelijke Taak & Bevoegdheid']), obprops=[])

    class Meta(Base_Schema.Meta):
        slug = 'belangen'
        table = 'Belangen'
        read_only = False
        ordered = True
        searchable = True


class Beleidsdoelen_Schema(Base_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_title'])
    Omschrijving = MM.fields.Str(missing=None, obprops=['search_description'])
    Weblink = MM.fields.Str(missing=None, obprops=[])

    class Meta(Base_Schema.Meta):
        slug = 'beleidsdoelen'
        table = 'Beleidsdoelen'
        read_only = False
        ordered = True
        searchable = True


class Beleidsprestaties_Schema(Base_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_title'])
    Omschrijving = MM.fields.Str(missing=None, obprops=['search_description'])
    Weblink = MM.fields.Str(missing=None, obprops=[])

    class Meta(Base_Schema.Meta):
        slug = 'beleidsprestaties'
        table = 'Beleidsprestaties'
        read_only = False
        ordered = True
        searchable = True


class Beleidsregels_Schema(Base_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_title'])
    Omschrijving = MM.fields.Str(missing=None, obprops=['search_description'])
    Weblink = MM.fields.Str(missing=None, obprops=[])

    class Meta(Base_Schema.Meta):
        slug = 'beleidsregels'
        table = 'Beleidsregels'
        read_only = False
        ordered = True
        searchable = True


class Beleidsrelaties_Schema(Base_Schema):
    Van_Beleidskeuze = MM.fields.UUID(
        required=True, allow_none=False, validate=MM.validate.NoneOf([null_uuid, ]), obprops=[])
    Naar_Beleidskeuze = MM.fields.UUID(
        required=True, allow_none=False, validate=MM.validate.NoneOf([null_uuid, ]), obprops=[])
    Titel = MM.fields.Str(required=True, obprops=['search_field'])
    Omschrijving = MM.fields.Str(missing=None, obprops=['search_field'])
    Status = MM.fields.Str(required=True, validate=MM.validate.OneOf(
        ['Open', 'Akkoord', 'NietAkkoord', 'Verbroken']), obprops=[])
    Aanvraag_Datum = MM.fields.DateTime(
        format='iso', required=True, obprops=[])
    Datum_Akkoord = MM.fields.DateTime(
        format='iso', allow_none=True, missing=None, obprops=[])

    class Meta(Base_Schema.Meta):
        slug = 'beleidsrelaties'
        table = 'Beleidsrelaties'
        read_only = False
        ordered = True
        searchable = False
        references = {
            'Van_Beleidskeuze': UUID_Reference('Beleidskeuzes',  Beleidskeuzes_Schema),
            'Naar_Beleidskeuze': UUID_Reference('Beleidskeuzes', Beleidskeuzes_Schema),

        }


class Maatregelen_Schema(Base_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_title'])
    Omschrijving = MM.fields.Str(missing=None, obprops=['search_description'])
    Toelichting = MM.fields.Str(missing=None, obprops=[])
    Toelichting_Raw = MM.fields.Method(missing=None, obprops=[])
    Status = MM.fields.Str(missing=None, validate=MM.validate.OneOf([
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
    Weblink = MM.fields.Str(missing=None, obprops=[])
    Gebied = MM.fields.UUID(missing=None, obprops=[])
    Gebied_Duiding = MM.fields.Str(allow_none=True, missing="Indicatief",
                                   validate=MM.validate.OneOf(["Indicatief", "Exact"]), obprops=[])
    Tags = MM.fields.Str(missing=None, obprops=[])
    Aanpassing_Op = MM.fields.UUID(
        missing=None, default=None, obprops=['excluded_post'])

    class Meta(Base_Schema.Meta):
        slug = 'maatregelen'
        table = 'Maatregelen'
        read_only = False
        ordered = True
        searchable = True
        references = {'Gebied': UUID_Reference(
            'Werkingsgebieden', Werkingsgebieden_Schema)}
        status_conf = ('Status', 'Vigerend')


class Themas_Schema(Base_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_title'])
    Omschrijving = MM.fields.Str(missing=None, obprops=['search_description'])
    Weblink = MM.fields.Str(missing=None, obprops=[])

    class Meta(Base_Schema.Meta):
        slug = 'themas'
        table = 'Themas'
        read_only = False
        ordered = True
        searchable = True


class Verordeningen_Schema(Base_Schema):
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
    Titel = MM.fields.Str(missing=None, obprops=['search_field'])
    Inhoud = MM.fields.Str(missing=None, obprops=['search_field'])
    Weblink = MM.fields.Str(missing=None, obprops=[])
    Status = MM.fields.Str(missing=None, obprops=['search_field'])
    Volgnummer = MM.fields.Str(missing=None, obprops=[])
    Type = MM.fields.Str(missing=None,  validate=MM.validate.OneOf(['Hoofdstuk', 'Afdeling', 'Paragraaf', 'Artikel', 'Lid']), obprops=['search_field'])
    Gebied = MM.fields.UUID(missing=None, obprops=[])

    class Meta(Base_Schema.Meta):
        slug = 'verordeningen'
        table = 'Verordeningen'
        read_only = False
        ordered = True
        searchable = False
        references =  references = {
            'Eigenaar_1': UUID_Reference('Gebruikers', Gebruikers_Schema),
            'Eigenaar_2': UUID_Reference('Gebruikers', Gebruikers_Schema),
            'Portefeuillehouder_1': UUID_Reference('Gebruikers', Gebruikers_Schema),
            'Portefeuillehouder_2': UUID_Reference('Gebruikers', Gebruikers_Schema),
            'Opdrachtgever': UUID_Reference('Gebruikers', Gebruikers_Schema),
            'Gebied': UUID_Reference('Werkingsgebieden', Werkingsgebieden_Schema)
        }


class Werkingsgebieden_Schema(Base_Schema):
    Werkingsgebied = MM.fields.Str(required=True, obprops=[])
    symbol = MM.fields.Str(missing=None, obprops=[])

    class Meta(Base_Schema.Meta):
        slug = 'werkingsgebieden'
        table = 'Werkingsgebieden'
        read_only = True
        ordered = True
        searchable = False