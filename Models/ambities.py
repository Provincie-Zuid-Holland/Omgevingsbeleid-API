# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from Endpoints.endpoint import Base_Schema


class Ambities_Schema(Base_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_field'])
    Omschrijving = MM.fields.Str(missing=None, obprops=['search_field'])
    Weblink = MM.fields.Str(missing=None, obprops=[])

    class Meta(Base_Schema.Meta):
        slug = 'ambities'
        table = 'Ambities'
        read_only = False
        ordered = True
        searchable = True
