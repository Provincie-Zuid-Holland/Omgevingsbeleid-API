# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from collections import namedtuple

from Models import (ambities, belangen, beleidsdoelen, beleidskeuzes,
                    beleidsprestaties, beleidsregels, gebruikers, maatregelen,
                    themas, werkingsgebieden)

Endpoint = namedtuple('Endpoint', ['slug', 'read_schema', 'write_schema'])

endpoints = [
    Endpoint('ambities', ambities.Ambities_Schema, ambities.Ambities_Schema),
    Endpoint('beleidskeuzes', beleidskeuzes.Beleidskeuzes_Schema,
             beleidskeuzes.Beleidskeuzes_Schema),
    Endpoint('belangen', belangen.Belangen_Schema, belangen.Belangen_Schema),
    Endpoint('beleidsdoelen', beleidsdoelen.Beleidsdoelen_Schema,
             beleidsdoelen.Beleidsdoelen_Schema),
    Endpoint('beleidsprestaties', beleidsprestaties.Beleidsprestaties_Schema,
             beleidsprestaties.Beleidsprestaties_Schema),
    Endpoint('beleidsregels', beleidsregels.Beleidsregels_Schema,
             beleidsregels.Beleidsregels_Schema),
    Endpoint('maatregelen', maatregelen.Maatregelen_Schema,
             maatregelen.Maatregelen_Schema),
    Endpoint('themas', themas.Themas_Schema, themas.Themas_Schema),
    Endpoint('werkingsgebieden', werkingsgebieden.Werkingsgebieden_Schema,
             werkingsgebieden.Werkingsgebieden_Schema)
]
