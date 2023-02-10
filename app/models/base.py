from enum import Enum, unique
from typing import Any, List, NamedTuple, Optional

from sqlalchemy import Column

from app.models import (
    Beleidsdoel_Ambities,
    Beleidskeuze_Belangen,
    Beleidskeuze_Beleidsdoelen,
    Beleidskeuze_Beleidsprestaties,
    Beleidskeuze_Beleidsregels,
    Beleidskeuze_Themas,
    Beleidskeuze_Verordeningen,
    Beleidskeuze_Werkingsgebieden,
    Beleidsmodule_Beleidskeuzes,
    Beleidsmodule_Gebiedsprogrammas,
    Beleidsmodule_Maatregelen,
    Maatregel_Gebiedsprogrammas,
)
from app.models.maatregel import Beleidskeuze_Maatregelen


@unique
class Status(str, Enum):
    """
    Enum interface of acceptable Status values which are stored
    as strings in the DB and not validated outside of the api.
    """

    DEFINITIEF_GS = "Definitief ontwerp GS"
    DEFINITIEF_GS_CONCEPT = "Definitief ontwerp GS concept"
    DEFINITIEF_PS = "Definitief ontwerp PS"
    NIET_ACTIEF = "Niet-Actief"
    ONTWERP_GS = "Ontwerp GS"
    ONTWERP_GS_CONCEPT = "Ontwerp GS Concept"
    ONTWERP_INSPRAAK = "Ontwerp in inspraak"
    ONTWERP_PS = "Ontwerp PS"
    UITGECHECKT = "Uitgecheckt"
    VASTGESTELD = "Vastgesteld"
    VIGEREND = "Vigerend"
    VIGEREND_GEARCHIVEERD = "Vigerend gearchiveerd"


@unique
class RelatieStatus(str, Enum):
    """
    Enum interface of acceptable Beleidsrelatie Status values which are stored
    as strings in the DB and not validated outside of the api.
    """

    OPEN = "Open"
    AKKOORD = "Akkoord"
    NIETAKKOORD = "NietAkkoord"
    VERBROKEN = "Verbroken"


@unique
class UserStatus(str, Enum):
    ACTIEF = "Actief"
    INACTIEF = "Inactief"


@unique
class BeleidsrelatieType(str, Enum):
    """
    Enum interface of acceptable Beleidsrelatie Status values which are stored
    as strings in the DB and not validated outside of the api.
    """

    Beleidskeuze = "beleidskeuzes"
    Beleidsrelatie = "beleidsrelaties"
    Beleidsmodule = "beleidsmodules"
    Ambitie = "ambities"
    Belang = "belangen"
    Beleidsdoel = "beleidsdoelen"
    Beleidsprestatie = "beleidsprestaties"
    Maatregel = "maatregelen"
    Thema = "themas"
    Werkingsgebied = "werkingsgebieden"
    Verordening = "verordeningen"
    Gebiedsprogramma = "gebiedsprogrammas"


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
        model=Beleidsdoel_Ambities,
        left=Beleidsdoel_Ambities.Beleidsdoel_UUID,
        right=Beleidsdoel_Ambities.Ambitie_UUID,
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
        model=Beleidskeuze_Maatregelen,
        left=Beleidskeuze_Maatregelen.Beleidskeuze_UUID,
        right=Beleidskeuze_Maatregelen.Maatregel_UUID,
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
        model=Beleidsmodule_Gebiedsprogrammas,
        left=Beleidsmodule_Gebiedsprogrammas.Beleidsmodule_UUID,
        right=Beleidsmodule_Gebiedsprogrammas.Gebiedsprogramma_UUID,
    ),
    MTMRelation(
        model=Maatregel_Gebiedsprogrammas,
        left=Maatregel_Gebiedsprogrammas.Maatregel_UUID,
        right=Maatregel_Gebiedsprogrammas.Gebiedsprogramma_UUID,
    ),
    # Beleidsrelatie should me manual
    # MTMRelation(
    #     model=Beleidsrelatie,
    #     left=Beleidsrelatie.Van_Beleidskeuze_UUID,
    #     right=Beleidsrelatie.Naar_Beleidskeuze_UUID,
    #     description="Omschrijving"
    # ),
]


def find_mtm_map(model) -> Optional[MTMRelation]:
    """
    Helper method to select the mtm mapping based on class or classname
    """
    mtm_class = None
    for mtm in MANY_TO_MANY_RELATIONS:
        if model == mtm.model:
            mtm_class = mtm
            break
        elif model == mtm.model.__tablename__:
            mtm_class = mtm
            break

    return mtm_class
