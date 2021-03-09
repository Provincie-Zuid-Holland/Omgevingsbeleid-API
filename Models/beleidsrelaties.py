# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from Endpoints.endpoint import Base_Schema
from Endpoints.references import UUID_Reference 
from Models.beleidskeuzes import Beleidskeuzes_Schema
from globals import null_uuid

class Beleidsrelaties_Schema(Base_Schema):
    Van_Beleidskeuze = MM.fields.UUID(required=True, allow_none=False, validate=MM.validate.NoneOf([null_uuid,]), obprops=[])
    Naar_Beleidskeuze = MM.fields.UUID(required=True, allow_none=False, validate=MM.validate.NoneOf([null_uuid,]), obprops=[])
    Titel = MM.fields.Str(required=True, obprops=['search_field'])
    Omschrijving = MM.fields.Str(missing=None, obprops=['search_field'])
    Status = MM.fields.Str(required=True, validate=MM.validate.OneOf(['Open', 'Akkoord', 'NietAkkoord', 'Verbroken']), obprops=[])
    Aanvraag_Datum = MM.fields.DateTime(format='iso', required=True, obprops=[])
    Datum_Akkoord = MM.fields.DateTime(format='iso', allow_none=True, missing=None, obprops=[])
    
    class Meta(Base_Schema.Meta):
        slug = 'beleidsrelaties'
        table = 'Beleidsrelaties'
        read_only = False
        ordered = True
        searchable = False
        references = {
            'Van_Beleidskeuze': UUID_Reference('Beleidskeuzes', Beleidskeuzes_Schema),
            'Naar_Beleidskeuze': UUID_Reference('Beleidskeuzes', Beleidskeuzes_Schema),

        }
    