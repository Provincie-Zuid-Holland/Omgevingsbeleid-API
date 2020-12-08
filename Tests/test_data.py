import marshmallow as MM
from globals import null_uuid

def generate_data(schema, user_UUID=null_uuid, excluded_prop = None):
    fields = schema(exclude=schema.fields_with_props(excluded_prop)).fields
    result = {}
    for field in fields:
        if field == 'Created_By' or field == 'Modified_By':
            result[field] = user_UUID
        elif isinstance(fields[field], MM.fields.Str) and not isinstance(fields[field], MM.fields.UUID):
            result[field] = "Test String"
        elif isinstance(fields[field], MM.fields.Integer):
            result[field] = 42
        elif isinstance(fields[field], MM.fields.DateTime):
            result[field] = '1992-11-23T10:00:00'
        else:
            raise NotImplementedError(f'Missing implementation for field {field} with value {fields[field]}')
    return result
