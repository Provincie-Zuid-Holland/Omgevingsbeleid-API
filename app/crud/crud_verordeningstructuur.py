from app.crud.base import CRUDBase
from app.models import Verordeningstructuur
from app.schemas.verordeningstructuur import (
    VerordeningstructuurUpdate,
    VerordeningstructuurCreate,
)


class CRUDVerordeningstructuur(
    CRUDBase[
        Verordeningstructuur, VerordeningstructuurCreate, VerordeningstructuurUpdate
    ]
):
    pass


verordeningstructuur = CRUDVerordeningstructuur(Verordeningstructuur)
