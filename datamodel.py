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
from Models.beleidsmodule import Beleidsmodule_Schema
from Models.short_schemas import Short_Beleidsmodule_Schema, Short_Beleidskeuze_Schema
import Endpoints.references as references

short_schemas = [Short_Beleidskeuze_Schema, Short_Beleidsmodule_Schema]

endpoints = [
    Beleidsrelaties_Schema,
    Beleidsmodule_Schema,
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
]

linker_tables = [
    ("Beleidskeuze_Ambities", "Ambitie_UUID"),
    ("Beleidskeuze_Belangen", "Belang_UUID"),
    ("Beleidskeuze_Beleidsdoelen", "Beleidsdoel_UUID"),
    ("Beleidskeuze_Beleidsprestaties", "Beleidsprestatie_UUID"),
    ("Beleidskeuze_Beleidsregels", "Beleidsregel_UUID"),
    ("Beleidskeuze_Maatregelen", "Maatregel_UUID"),
    ("Beleidskeuze_Themas", "Thema_UUID"),
    ("Beleidskeuze_Verordeningen", "Verordening_UUID"),
    ("Beleidskeuze_Werkingsgebieden", "Werkingsgebied_UUID"),
]


def show_inlined_properties():
    """We use this to help the frontend."""
    for ep in endpoints:
        print(ep.Meta.slug)
        for ref in ep.Meta.references:
            if isinstance(ep.Meta.references[ref], references.UUID_List_Reference):
                print(
                    "\t", ref, f": Lijst naar {ep.Meta.references[ref].their_tablename}"
                )
            if isinstance(ep.Meta.references[ref], references.UUID_Reference):
                print(
                    "\t",
                    ref,
                    f": Enkele naar {ep.Meta.references[ref].target_tablename}",
                )
            if isinstance(ep.Meta.references[ref], references.Reverse_UUID_Reference):
                print(
                    "\t",
                    ref,
                    f": Reverse van {ep.Meta.references[ref].their_tablename}",
                )
