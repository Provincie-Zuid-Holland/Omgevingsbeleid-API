# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM

from Endpoints.endpoint import Base_Schema
from Endpoints.references import UUID_Reference

from Models.gebruikers import Gebruikers_Schema
from Models.werkingsgebieden import Werkingsgebieden_Schema

from globals import default_user_uuid

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
