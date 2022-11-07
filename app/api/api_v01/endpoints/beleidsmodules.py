from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound

from app import models, schemas
from app.api import deps
from app.crud import CRUDBeleidsmodule
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
    crud_beleidsmodule: CRUDBeleidsmodule = Depends(deps.get_crud_beleidsmodule),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsmodules lineages and shows the latests object for each
    """
    beleidsmodules = crud_beleidsmodule.latest(
        all=True, filters=filters, offset=offset, limit=limit
    )

    return beleidsmodules


@router.post("/beleidsmodules", response_model=schemas.Beleidsmodule)
def create_beleidsmodule(
    *,
    beleidsmodule_in: schemas.BeleidsmoduleCreate,
    crud_beleidsmodule: CRUDBeleidsmodule = Depends(deps.get_crud_beleidsmodule),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new beleidsmodules lineage
    """
    beleidsmodule = crud_beleidsmodule.create(
        obj_in=beleidsmodule_in, by_uuid=current_gebruiker.UUID
    )
    return beleidsmodule


@router.get("/beleidsmodules/{lineage_id}", response_model=List[schemas.Beleidsmodule])
def read_beleidsmodule_lineage(
    *,
    lineage_id: int,
    crud_beleidsmodule: CRUDBeleidsmodule = Depends(deps.get_crud_beleidsmodule),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the beleidsmodules versions by lineage
    """
    beleidsmodules = crud_beleidsmodule.all(filters=Filters({"ID": lineage_id}))
    if not beleidsmodules:
        raise HTTPException(status_code=404, detail="Beleidsmodules not found")
    return beleidsmodules


@router.patch("/beleidsmodules/{lineage_id}", response_model=schemas.Beleidsmodule)
def update_beleidsmodule(
    *,
    lineage_id: int,
    beleidsmodule_in: schemas.BeleidsmoduleUpdate,
    crud_beleidsmodule: CRUDBeleidsmodule = Depends(deps.get_crud_beleidsmodule),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new beleidsmodules to a lineage
    """
    beleidsmodule = crud_beleidsmodule.get_latest_by_id(id=lineage_id)
    if not beleidsmodule:
        raise HTTPException(status_code=404, detail="Beleidsmodule not found")
    if beleidsmodule.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    beleidsmodule = crud_beleidsmodule.update(
        db_obj=beleidsmodule, obj_in=beleidsmodule_in
    )
    return beleidsmodule


@router.get("/changes/beleidsmodules/{old_uuid}/{new_uuid}")
def changes_beleidsmodules(
    old_uuid: str,
    new_uuid: str,
    crud_beleidsmodule: CRUDBeleidsmodule = Depends(deps.get_crud_beleidsmodule),
) -> Any:
    """
    Shows the changes between two versions of beleidsmodules.
    """
    try:
        old = crud_beleidsmodule.get(old_uuid)
        new = crud_beleidsmodule.get(new_uuid)
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
    crud_beleidsmodule: CRUDBeleidsmodule = Depends(deps.get_crud_beleidsmodule),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsmodules lineages and shows the latests valid object for each.
    """
    beleidsmodules = crud_beleidsmodule.valid(
        offset=offset, limit=limit, filters=filters
    )
    return beleidsmodules


@router.get(
    "/valid/beleidsmodules/{lineage_id}", response_model=List[schemas.Beleidsmodule]
)
def read_valid_beleidsmodule_lineage(
    lineage_id: int,
    crud_beleidsmodule: CRUDBeleidsmodule = Depends(deps.get_crud_beleidsmodule),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsmodules in this lineage that are valid
    """
    beleidsmodules = crud_beleidsmodule.valid(
        ID=lineage_id, offset=offset, limit=limit, filters=filters
    )
    return beleidsmodules
