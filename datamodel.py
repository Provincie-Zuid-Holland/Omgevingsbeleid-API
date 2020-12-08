from Dimensies import ambitie, gebruikers
from collections import namedtuple


Endpoint = namedtuple('Endpoint', ['slug', 'read_schema', 'write_schema'])

normal_endpoints = [
    Endpoint('ambities', ambitie.Ambitie_Schema, ambitie.Ambitie_Schema)
]

feiten = []

def all_endpoints():
    return normal_endpoints