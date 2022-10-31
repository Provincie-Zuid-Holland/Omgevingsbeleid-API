from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from app import crud, models, schemas
from app.api import deps
from app.models.gebruiker import GebruikersRol
from app.schemas.filters import Filters
from app.util.compare import Comparator

router = APIRouter()

defer_attributes = {
    "Omschrijving",
    "Externe_URL",
    "Weblink",
}


@router.get(
    "/beleidsregels",
    response_model=List[schemas.Beleidsregel],
    response_model_exclude=defer_attributes,
)
def read_beleidsregels(
    db: Session = Depends(deps.get_db),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsregels lineages and shows the latests object for each
    """
    beleidsregels = crud.beleidsregel.latest(
        all=True, filters=filters, offset=offset, limit=limit
    )

    return beleidsregels


@router.post("/beleidsregels", response_model=schemas.Beleidsregel)
def create_beleidsregel(
    *,
    db: Session = Depends(deps.get_db),
    beleidsregel_in: schemas.BeleidsregelCreate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new beleidsregels lineage
    """
    beleidsregel = crud.beleidsregel.create(
        obj_in=beleidsregel_in, by_uuid=current_gebruiker.UUID
    )
    return beleidsregel


@router.get("/beleidsregels/{lineage_id}", response_model=List[schemas.Beleidsregel])
def read_beleidsregel_lineage(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
) -> Any:
    """
    Gets all the beleidsregels versions by lineage
    """
    beleidsregels = crud.beleidsregel.all(filters=Filters({"ID": lineage_id}))
    if not beleidsregels:
        raise HTTPException(status_code=404, detail="Beleidsregels not found")
    return beleidsregels


@router.patch("/beleidsregels/{lineage_id}", response_model=schemas.Beleidsregel)
def update_beleidsregel(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    beleidsregel_in: schemas.BeleidsregelUpdate,
) -> Any:
    """
    Adds a new beleidsregels to a lineage
    """
    beleidsregel = crud.beleidsregel.get_latest_by_id(id=lineage_id)
    if not beleidsregel:
        raise HTTPException(status_code=404, detail="Beleidsregel not found")
    if beleidsregel.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    beleidsregel = crud.beleidsregel.update(db_obj=beleidsregel, obj_in=beleidsregel_in)
    return beleidsregel


@router.get("/changes/beleidsregels/{old_uuid}/{new_uuid}")
def changes_beleidsregels(
    old_uuid: str,
    new_uuid: str,
) -> Any:
    """
    Shows the changes between two versions of beleidsregels.
    """
    try:
        old = crud.beleidsregel.get(old_uuid)
        new = crud.beleidsregel.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )

    json_data = Comparator(
        schema=schemas.Beleidsregel, old=old, new=new
    ).get_json_result()
    return JSONResponse(content=json_data)


@router.get(
    "/valid/beleidsregels",
    response_model=List[schemas.Beleidsregel],
    response_model_exclude=defer_attributes,
)
def read_valid_beleidsregels(
    db: Session = Depends(deps.get_db),
    offset: int = 0,
    limit: int = 20,
    filters: Filters = Depends(deps.string_filters),
) -> Any:
    """
    Gets all the beleidsregels lineages and shows the latests valid object for each.
    """
    beleidsregels = crud.beleidsregel.valid(offset=offset, limit=limit, filters=filters)
    return beleidsregels


@router.get(
    "/valid/beleidsregels/{lineage_id}", response_model=List[schemas.Beleidsregel]
)
def read_valid_beleidsregel_lineage(
    lineage_id: int,
    offset: int = 0,
    limit: int = 20,
    filters: Filters = Depends(deps.string_filters),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Gets all the beleidsregels in this lineage that are valid
    """
    beleidsregels = crud.beleidsregel.valid(
        ID=lineage_id, offset=offset, limit=limit, filters=filters
    )
    return beleidsregels
