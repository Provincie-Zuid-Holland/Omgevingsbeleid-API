# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from Endpoints.endpoint import Base_Schema


class Werkingsgebieden_Schema(Base_Schema):
    Werkingsgebied = MM.fields.Str(required=True, obprops=['short'])
    symbol = MM.fields.Str(missing=None, obprops=['short'])

    class Meta(Base_Schema.Meta):
        slug = 'werkingsgebieden'
        table = 'Werkingsgebieden'
        read_only = True
        ordered = True
        searchable = False
