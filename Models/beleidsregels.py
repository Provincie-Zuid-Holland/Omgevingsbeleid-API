# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from Endpoints.endpoint import Base_Schema
from Endpoints.validators import HTML_Validate

class Beleidsregels_Schema(Base_Schema):
    Titel = MM.fields.Str(required=True, validate=[HTML_Validate], obprops=['search_title'])
    Omschrijving = MM.fields.Str(missing=None, validate=[HTML_Validate], obprops=['search_description'])
    Weblink = MM.fields.Str(missing=None, obprops=[])

    class Meta(Base_Schema.Meta):
        slug = 'beleidsregels'
        table = 'Beleidsregels'
        read_only = False
        ordered = True
        searchable = True