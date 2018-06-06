from cerberus import Validator

themaValidator = Validator({
    'naam':
        {'type': 'string', 
        'required': True,
        'empty':False},
    'beschrijving':
        {'type': 'string', 
        'required': False},
    'opgaven':
        {'type': 'list', 'schema': {'type': 'integer', 'coerce':int}},
})
