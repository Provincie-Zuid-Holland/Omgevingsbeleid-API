from Dimensies import ambitie, gebruikers
from collections import namedtuple


Dimensie = namedtuple('Dimensie', ['slug', 'read_schema', 'write_schema'])

dimensies = [
    Dimensie('ambities', ambitie.Ambitie_Schema, ambitie.Ambitie_Schema)
]

feiten = []

# Normalized union of Dimensies en Feiten for use in search
def dimensies_and_feiten():
    return dimensies + feiten