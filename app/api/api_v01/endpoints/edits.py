import logging
from typing import Any, List

from fastapi import APIRouter, Depends

from app import schemas
from app.api.deps import get_crud_beleidskeuze, get_crud_maatregel
from app.crud.crud_beleidskeuze import CRUDBeleidskeuze
from app.crud.crud_maatregel import CRUDMaatregel

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/edits",
    response_model=List[schemas.LatestVersionInline],
)
def edits(
    crud_beleidskeuze: CRUDBeleidskeuze = Depends(get_crud_beleidskeuze),
    crud_maatregel: CRUDMaatregel = Depends(get_crud_maatregel),
) -> Any:
    """
    Get the latest edits for every lineage,
    active for 'Beleidskeuzes' & 'Maatregelen'
    """
    # Beleidskeuzes
    result_beleidskeuzes = crud_beleidskeuze.latest(all=True, limit=50)
    for bk in result_beleidskeuzes:
        setattr(bk, "Type", "beleidskeuze")

    # Maatregelen
    result_maatregelen = crud_maatregel.latest(all=True, offset=0, limit=50)
    for maat in result_maatregelen:
        setattr(maat, "Type", "maatregel")

    return result_beleidskeuzes + result_maatregelen
