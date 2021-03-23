# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from Endpoints.endpoint import Base_Schema
from Endpoints.validators import HTML_Validate
from .beleidskeuzes_short import Short_Beleidskeuze_Schema
from Endpoints.references import UUID_Linker_Schema, Reverse_UUID_Reference

class Belangen_Schema(Base_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_title'])
    Omschrijving = MM.fields.Str(missing=None,validate=[HTML_Validate], obprops=['search_description'])
    Weblink = MM.fields.Str(missing=None, obprops=[ ])
    Type = MM.fields.Str(missing=None, validate=[MM.validate.OneOf(['Nationaal Belang', 'Wettelijke Taak & Bevoegdheid'])], obprops=[])
    Ref_Beleidskeuzes = MM.fields.Nested(
        UUID_Linker_Schema, many=True, obprops=['referencelist', 'excluded_patch', 'excluded_post'])

    class Meta(Base_Schema.Meta):
        slug = 'belangen'
        table = 'Belangen'
        read_only = False
        ordered = True
        searchable = True
        references = {
            'Ref_Beleidskeuzes':Reverse_UUID_Reference('Beleidskeuze_Belangen',
                                                 'Beleidskeuzes',
                                                 'Belang_UUID',
                                                 'Beleidskeuze_UUID',
                                                 'Koppeling_Omschrijving',
                                                 Short_Beleidskeuze_Schema
                                                 )
        }
