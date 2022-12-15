from typing import Any, List, NamedTuple

from sqlalchemy import Column

from app.models import (
    Beleidskeuze_Ambities,
    Beleidskeuze_Belangen,
    Beleidskeuze_Beleidsdoelen,
    Beleidskeuze_Beleidsprestaties,
    Beleidskeuze_Beleidsregels,
    Beleidskeuze_Themas,
    Beleidskeuze_Verordeningen,
    Beleidskeuze_Werkingsgebieden,
    Beleidsmodule_Beleidskeuzes,
    Beleidsmodule_Maatregelen,
)
from app.models.beleidsrelatie import Beleidsrelatie


class MTMRelation(NamedTuple):
    """
    Typed NamedTuple helper to generically map
    many-to-many relationships with their foreignkey columns
    """

    model: Any
    left: Column
    right: Column
    description: str = "Koppeling_Omschrijving"


MANY_TO_MANY_RELATIONS: List[MTMRelation] = [
    MTMRelation(
        model=Beleidskeuze_Ambities,
        left=Beleidskeuze_Ambities.Beleidskeuze_UUID,
        right=Beleidskeuze_Ambities.Ambitie_UUID,
    ),
    MTMRelation(
        model=Beleidskeuze_Belangen,
        left=Beleidskeuze_Belangen.Beleidskeuze_UUID,
        right=Beleidskeuze_Belangen.Belang_UUID,
    ),
    MTMRelation(
        model=Beleidskeuze_Beleidsdoelen,
        left=Beleidskeuze_Beleidsdoelen.Beleidskeuze_UUID,
        right=Beleidskeuze_Beleidsdoelen.Beleidsdoel_UUID,
    ),
    MTMRelation(
        model=Beleidskeuze_Beleidsprestaties,
        left=Beleidskeuze_Beleidsprestaties.Beleidskeuze_UUID,
        right=Beleidskeuze_Beleidsprestaties.Beleidsprestatie_UUID,
    ),
    MTMRelation(
        model=Beleidskeuze_Beleidsregels,
        left=Beleidskeuze_Beleidsregels.Beleidskeuze_UUID,
        right=Beleidskeuze_Beleidsregels.Beleidsregel_UUID,
    ),
    MTMRelation(
        model=Beleidskeuze_Themas,
        left=Beleidskeuze_Themas.Beleidskeuze_UUID,
        right=Beleidskeuze_Themas.Thema_UUID,
    ),
    MTMRelation(
        model=Beleidskeuze_Verordeningen,
        left=Beleidskeuze_Verordeningen.Beleidskeuze_UUID,
        right=Beleidskeuze_Verordeningen.Verordening_UUID,
    ),
    MTMRelation(
        model=Beleidskeuze_Werkingsgebieden,
        left=Beleidskeuze_Werkingsgebieden.Beleidskeuze_UUID,
        right=Beleidskeuze_Werkingsgebieden.Werkingsgebied_UUID,
    ),
    MTMRelation(
        model=Beleidsmodule_Beleidskeuzes,
        left=Beleidsmodule_Beleidskeuzes.Beleidsmodule_UUID,
        right=Beleidsmodule_Beleidskeuzes.Beleidskeuze_UUID,
    ),
    MTMRelation(
        model=Beleidsmodule_Maatregelen,
        left=Beleidsmodule_Maatregelen.Beleidsmodule_UUID,
        right=Beleidsmodule_Maatregelen.Maatregel_UUID,
    ),
    MTMRelation(
        model=Beleidsrelatie,
        left=Beleidsrelatie.Van_Beleidskeuze_UUID,
        right=Beleidsrelatie.Naar_Beleidskeuze_UUID,
    ),
]

# TODO: Base model ABC SQLALCHEMY
# https://sqlalchemy-utils.readthedocs.io/en/latest/generic_relationship.html#abstract-base-classes

