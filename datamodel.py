# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from Models import models

endpoints = [
    models.Beleidskeuzes_Schema,
    models.Ambities_Schema,
    models.Belangen_Schema,
    models.Beleidsdoelen_Schema,
    models.Beleidsprestaties_Schema,
    models.Beleidsregels_Schema,
    models.Maatregelen_Schema,
    models.Themas_Schema,
    models.Werkingsgebieden_Schema,
    models.Verordeningen_Schema,
    models.Beleidsrelaties_Schema
]

registry = {(ep.Meta.slug, ep) for ep in endpoints}