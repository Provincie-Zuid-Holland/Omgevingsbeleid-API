# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from Endpoints.endpoint import Base_Schema
from Endpoints.references import UUID_Reference, UUID_List_Reference, UUID_Linker_Schema

class Ambities_Schema(Base_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_title'])
    Omschrijving = MM.fields.Str(missing=None, obprops=['search_description'])
    Weblink = MM.fields.Str(missing=None, obprops=[])
    # Beleidskeuzes = MM.fields.Nested(
        # UUID_Linker_Schema, many=True, obprops=['referencelist'])

    class Meta(Base_Schema.Meta):
        slug = 'ambities'
        table = 'Ambities'
        read_only = False
        ordered = True
        searchable = True
        # references = {
        #     'Beleidskeuzes': UUID_List_Reference('Beleidskeuze_Ambities',
        #                                          'Beleidskeuzes',
        #                                          'Ambitie_UUID',
        #                                          'Beleidskeuze_UUID',
        #                                         Models.beleidskeuzes.Beleidskeuzes_Schema
        #                                          )
        # }