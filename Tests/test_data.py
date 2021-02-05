# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from globals import null_uuid
from Endpoints.custom_fields import UUID_ReferenceList

def generate_data(schema, user_UUID=null_uuid, excluded_prop = None):
    fields = schema(exclude=schema.fields_with_props(excluded_prop)).fields
    result = {}
    for field in fields:
        if fields[field].validate:
            try:
                result[field] = fields[field].validate.choices[0]
            except AttributeError:
                continue   
        
        elif field == 'Created_By' or field == 'Modified_By':
            result[field] = user_UUID
        
        elif field =='Status':
            result[field] = 'Niet-Actief'
        
        elif type(fields[field]) == MM.fields.String:
            result[field] = "Test String"
        
        elif type(fields[field]) == MM.fields.UUID:
            result[field] = null_uuid
            
        elif type(fields[field]) == MM.fields.Integer:
            result[field] = 42

        elif type(fields[field]) == MM.fields.DateTime:
            result[field] = '1992-11-23T10:00:00'
        
        elif type(fields[field]) == MM.fields.Method:
            result[field] = ''

        elif type(fields[field]) == MM.fields.Nested:
            result[field] = []

        else:
            raise NotImplementedError(f'Missing implementation for field {field} ({type(fields[field])}) with value {fields[field]}')
    return result


reference_rich_beleidskeuze ={
    "Status": "Vigerend",
    "Titel": "Beleidsbeslissing test Swen Initial",
    "Begin_Geldigheid": "2020-10-28T12:00:00",
    "Eind_Geldigheid": "2020-10-30T12:00:00",
    "Aanleiding": "Om te testen",
    "Afweging": "Zonder aanleiding",
    "Omschrijving_Keuze": "Nam libero leo, tempus in pretium vel, rhoncus in mi.",
    "Omschrijving_Werking": "Duis neque nulla, egestas aliquet nisi ut, dapibus pellentesque neque.",
    "Provinciaal_Belang": "In het belang van de wetenschap",
    "Weblink": "www.beleid.beslissing.nl",
    "Besluitnummer": "42",
    "Tags": "Wetenschap, Test",
    "Ambities": [
        {
            "UUID": "B786487C-3E65-4DD8-B360-D2C56BF83172",
            "Koppeling_Omschrijving": "TEST"
        },
        {
            "UUID": "0254A475-08A6-4B2A-A455-96BA6BE70A19",
            "Koppeling_Omschrijving": "TEST"
        }
    ]
}