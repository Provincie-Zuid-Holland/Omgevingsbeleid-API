# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM

from Endpoints.endpoint import Base_Schema
from Endpoints.references import UUID_Reference, UUID_List_Reference, UUID_Linker_Schema, ID_List_Reference
from Endpoints.validators import HTML_Validate

from globals import default_user_uuid, min_datetime

import Models.maatregelen
import Models.beleidskeuzes


class Beleidsmodule_Schema(Base_Schema):
    Titel = MM.fields.Str(required=True, obprops=[])
    Besluit_Datum = MM.fields.DateTime(format='iso', 
        missing=min_datetime, allow_none=True, obprops=[])
    Maatregelen = MM.fields.Nested(
        UUID_Linker_Schema, many=True, obprops=['referencelist'])
    Beleidskeuzes = MM.fields.Nested(
        UUID_Linker_Schema, many=True, obprops=['referencelist'])

    class Meta(Base_Schema.Meta):
        slug = 'beleidsmodules'
        table = 'Beleidsmodules'
        read_only = False
        ordered = True
        searchable = False
        references = {
            'Maatregelen': UUID_List_Reference('Beleidsmodule_Maatregelen', 'Maatregelen', 'Beleidsmodule_UUID', 'Maatregel_UUID', 'Koppeling_Omschrijving', Models.maatregelen.Maatregelen_Schema),
            'Beleidskeuzes': UUID_List_Reference('Beleidsmodule_Beleidskeuzes', 'Beleidskeuzes', 'Beleidsmodule_UUID', 'Beleidskeuze_UUID', 'Koppeling_Omschrijving', Models.beleidskeuzes.Beleidskeuzes_Schema)
        }