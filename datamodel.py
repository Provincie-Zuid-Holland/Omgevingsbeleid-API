# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from Models import ambitie, gebruikers, beleidskeuze
from collections import namedtuple


Endpoint = namedtuple('Endpoint', ['slug', 'read_schema', 'write_schema'])

endpoints = [
    Endpoint('ambities', ambitie.Ambitie_Schema, ambitie.Ambitie_Schema),
    Endpoint('beleidskeuzes', beleidskeuze.Beleidskeuze_Schema, beleidskeuze.Beleidskeuze_Schema)
]


def all_endpoints():
    return endpoints