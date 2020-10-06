from endpoints.schemas.ambitie import Ambitie_Schema
from collections import namedtuple

Endpoint = namedtuple('Endpoint', ['slug', 'read_schema', 'write_schema'])

endpoints = [
    Endpoint('ambities', Ambitie_Schema, Ambitie_Schema)
]
