# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from Models import (ambities, belangen, beleidsdoelen, beleidskeuzes,
                    beleidsprestaties, beleidsregels, gebruikers, maatregelen,
                    themas, werkingsgebieden, verordeningen)


endpoints = [
    beleidskeuzes.Beleidskeuzes_Schema,
    ambities.Ambities_Schema,
    belangen.Belangen_Schema,
    beleidsdoelen.Beleidsdoelen_Schema,
    beleidsprestaties.Beleidsprestaties_Schema,
    beleidsregels.Beleidsregels_Schema,
    maatregelen.Maatregelen_Schema,
    themas.Themas_Schema,
    werkingsgebieden.Werkingsgebieden_Schema,
    verordeningen.Verordeningen_Schema
]
