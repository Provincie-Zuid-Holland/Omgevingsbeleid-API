# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from Endpoints.endpoint import Base_Schema


class Belangen_Schema(Base_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_field'])
    Omschrijving = MM.fields.Str(missing=None, obprops=['search_field'])
    Weblink = MM.fields.Str(missing=None, obprops=[ ])
    Type = MM.fields.Str(required=True, validate=[MM.validate.OneOf(['Nationaal Belang', 'Wettelijke Taak & Bevoegdheid']), ], obprops=[])

    class Meta(Base_Schema.Meta):
        table = 'Belangen'
        read_only = False
        ordered = True
        searchable = True
