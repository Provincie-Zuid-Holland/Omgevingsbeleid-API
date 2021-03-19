# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from Endpoints.base_schema import Base_Schema, Short_Base_Schema
from Endpoints.references import UUID_Reference, UUID_List_Reference, UUID_Linker_Schema



# For reverse lookups we have to define a custom schema in order to prevent circulair imports
class Short_Beleidskeuze_Schema(Short_Base_Schema):
    ID = MM.fields.Integer(required=True, obprops=[])
    UUID = MM.fields.UUID(required=True, obprops=[])
    Titel = MM.fields.Str(required=True, obprops=[])

class Ambities_Schema(Base_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_title'])
    Omschrijving = MM.fields.Str(missing=None, obprops=['search_description'])
    Weblink = MM.fields.Str(missing=None, obprops=[])
    Beleidskeuzes = MM.fields.Nested(
        UUID_Linker_Schema, many=True, obprops=['referencelist', 'excluded_patch', 'excluded_post'])

    class Meta(Base_Schema.Meta):
        slug = 'ambities'
        table = 'Ambities'
        read_only = False
        ordered = True
        searchable = True
        references = {
            'Beleidskeuzes': UUID_List_Reference('Beleidskeuze_Ambities',
                                                 'Beleidskeuzes',
                                                 'Ambitie_UUID',
                                                 'Beleidskeuze_UUID',
                                                 'Koppeling_Omschrijving',
                                                 Short_Beleidskeuze_Schema
                                                 )
        }
