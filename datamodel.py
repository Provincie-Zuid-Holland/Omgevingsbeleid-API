# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from Models.beleidskeuzes import Beleidskeuzes_Schema
from Models.ambities import Ambities_Schema
from Models.belangen import Belangen_Schema
from Models.beleidsdoelen import Beleidsdoelen_Schema
from Models.beleidsprestaties import Beleidsprestaties_Schema
from Models.beleidsregels import Beleidsregels_Schema
from Models.maatregelen import Maatregelen_Schema
from Models.themas import Themas_Schema
from Models.werkingsgebieden import Werkingsgebieden_Schema
from Models.verordeningen import Verordeningen_Schema
from Models.beleidsrelaties import Beleidsrelaties_Schema

endpoints = [
    Beleidskeuzes_Schema,
    Ambities_Schema,
    Belangen_Schema,
    Beleidsdoelen_Schema,
    Beleidsprestaties_Schema,
    Beleidsregels_Schema,
    Maatregelen_Schema,
    Themas_Schema,
    Werkingsgebieden_Schema,
    Verordeningen_Schema,
    Beleidsrelaties_Schema
]

