from marshmallow import fields, ValidationError
import uuid

class UUID_ReferenceList(fields.Nested):
    """
    Field that serializes to a list of UUIDs and deserializes
    to a list of inline schemas.
    """

    # def __init__(self, nested_schema, **kwargs):
    #     super().__init__(**kwargs)
    #     self.nested_schema = nested_schema
    
    # def _serialize(self, value, attr, obj, **kwags):
    #     # Python -> text
    #     pass

    # def _deserialize(self, value, attr, data, **kwargs):
    #     # text -> python
    #     try:
    #         [uuid.UUID(_uuid) for _uuid in value]
    #     except:
    #         raise ValidationError('Values needs to be an UUID')
    #     return value