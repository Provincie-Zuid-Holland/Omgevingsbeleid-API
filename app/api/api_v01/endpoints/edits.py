from datetime import datetime
import logging
from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import get_crud_beleidskeuze, get_crud_maatregel, get_db
from app.crud.crud_beleidskeuze import CRUDBeleidskeuze
from app.crud.crud_maatregel import CRUDMaatregel

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/edits",
    response_model=List[schemas.LatestVersionInline],
)
def edits(
    db: Session = Depends(get_db),
    crud_beleidskeuze: CRUDBeleidskeuze = Depends(get_crud_beleidskeuze),
    crud_maatregel: CRUDMaatregel = Depends(get_crud_maatregel),
) -> Any:
    """
    Get the latest edits for every lineage,
    active for 'Beleidskeuzes' & 'Maatregelen'
    """
    # TODO: DRY and query performance

    # Beleidskeuzes
    result_beleidskeuzes = crud_beleidskeuze.latest(all=True, limit=50)

    maatregel_subq = crud_beleidskeuze._build_valid_inner_query().subquery("inner")
    maatregel_valid_query = (
        db.query(maatregel_subq.c.get("UUID"), maatregel_subq.c.get("ID"))
        .filter(maatregel_subq.c.get("RowNumber") == 1)
        .filter(maatregel_subq.c.get("Eind_Geldigheid") > datetime.utcnow())
    )

    valid_ids = dict()
    for valid in maatregel_valid_query:
        valid_ids[valid[1]] = valid[0]

    for bk in result_beleidskeuzes:
        setattr(bk, "Type", "beleidskeuze")
        if bk.ID in valid_ids:
            setattr(bk, "Effective_Version", valid_ids[bk.ID])

    # Maatregelen
    result_maat = crud_maatregel.latest(all=True, offset=0, limit=50)

    maatregel_subq = crud_maatregel._build_valid_inner_query().subquery("inner")
    maatregel_valid_query = (
        db.query(maatregel_subq.c.get("UUID"), maatregel_subq.c.get("ID"))
        .filter(maatregel_subq.c.get("RowNumber") == 1)
        .filter(maatregel_subq.c.get("Eind_Geldigheid") > datetime.utcnow())
    )

    valid_ids = dict()
    for valid in maatregel_valid_query:
        valid_ids[valid[1]] = valid[0]

    for maatregel in result_maat:
        setattr(maatregel, "Type", "maatregel")
        if maatregel.ID in valid_ids:
            setattr(maatregel, "Effective_Version", valid_ids[maatregel.ID])

    return result_beleidskeuzes + result_maat
