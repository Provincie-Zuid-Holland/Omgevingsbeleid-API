# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
from globals import null_uuid

def generate_data(schema, user_UUID=null_uuid, excluded_prop = None):
    fields = schema(exclude=schema.fields_with_props(excluded_prop)).fields
    result = {}
    for field in fields:
        if fields[field].validate:
            result[field] = fields[field].validate.choices[0]
        
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

        else:
            raise NotImplementedError(f'Missing implementation for field {field} ({type(fields[field])}) with value {fields[field]}')
    return result
