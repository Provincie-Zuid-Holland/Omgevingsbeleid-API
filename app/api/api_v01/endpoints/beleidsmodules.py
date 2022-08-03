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

defer_attributes = {"Omschrijving"}


@router.get(
    "/beleidsmodules",
    response_model=List[schemas.Beleidsmodule],
    response_model_exclude=defer_attributes,
)
def read_beleidsmodules(
    db: Session = Depends(deps.get_db),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsmodules lineages and shows the latests object for each
    """
    beleidsmodules = crud.beleidsmodule.latest(
        all=True, filters=filters, offset=offset, limit=limit
    )

    return beleidsmodules


@router.post("/beleidsmodules", response_model=schemas.Beleidsmodule)
def create_beleidsmodule(
    *,
    db: Session = Depends(deps.get_db),
    beleidsmodule_in: schemas.BeleidsmoduleCreate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new beleidsmodules lineage
    """
    beleidsmodule = crud.beleidsmodule.create(
        obj_in=beleidsmodule_in, by_uuid=current_gebruiker.UUID
    )
    return beleidsmodule


@router.get("/beleidsmodules/{lineage_id}", response_model=List[schemas.Beleidsmodule])
def read_beleidsmodule_lineage(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the beleidsmodules versions by lineage
    """
    beleidsmodules = crud.beleidsmodule.all(filters=Filters({"ID": lineage_id}))
    if not beleidsmodules:
        raise HTTPException(status_code=404, detail="Beleidsmodules not found")
    return beleidsmodules


@router.patch("/beleidsmodules/{lineage_id}", response_model=schemas.Beleidsmodule)
def update_beleidsmodule(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    beleidsmodule_in: schemas.BeleidsmoduleUpdate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new beleidsmodules to a lineage
    """
    beleidsmodule = crud.beleidsmodule.get_latest_by_id(id=lineage_id)
    if not beleidsmodule:
        raise HTTPException(status_code=404, detail="Beleidsmodule not found")
    if beleidsmodule.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    beleidsmodule = crud.beleidsmodule.update(
        db_obj=beleidsmodule, obj_in=beleidsmodule_in
    )
    return beleidsmodule


@router.get("/changes/beleidsmodules/{old_uuid}/{new_uuid}")
def changes_beleidsmodules(
    old_uuid: str,
    new_uuid: str,
) -> Any:
    """
    Shows the changes between two versions of beleidsmodules.
    """
    try:
        old = crud.beleidsmodule.get(old_uuid)
        new = crud.beleidsmodule.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )

    json_data = Comparator(
        schema=schemas.Beleidsmodule, old=old, new=new
    ).get_json_result()
    return JSONResponse(content=json_data)


@router.get(
    "/valid/beleidsmodules",
    response_model=List[schemas.Beleidsmodule],
    response_model_exclude=defer_attributes,
)
def read_valid_beleidsmodules(
    db: Session = Depends(deps.get_db),
    offset: int = 0,
    limit: int = 20,
    filters: Filters = Depends(deps.string_filters),
) -> Any:
    """
    Gets all the beleidsmodules lineages and shows the latests valid object for each.
    """
    beleidsmodules = crud.beleidsmodule.valid(
        offset=offset, limit=limit, filters=filters
    )
    return beleidsmodules


@router.get(
    "/valid/beleidsmodules/{lineage_id}", response_model=List[schemas.Beleidsmodule]
)
def read_valid_beleidsmodule_lineage(
    lineage_id: int,
    offset: int = 0,
    limit: int = 20,
    filters: Filters = Depends(deps.string_filters),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Gets all the beleidsmodules in this lineage that are valid
    """
    beleidsmodules = crud.beleidsmodule.valid(ID=lineage_id, offset=offset, limit=limit, filters=filters)
    return beleidsmodules
