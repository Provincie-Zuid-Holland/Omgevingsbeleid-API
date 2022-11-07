from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from app import crud, models, schemas
from app.api import deps
from app.crud import CRUDBeleidsregel
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
    crud_beleidsregel: CRUDBeleidsregel = Depends(deps.get_crud_beleidsregel),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsregels lineages and shows the latests object for each
    """
    beleidsregels = crud_beleidsregel.latest(
        all=True, filters=filters, offset=offset, limit=limit
    )

    return beleidsregels


@router.post("/beleidsregels", response_model=schemas.Beleidsregel)
def create_beleidsregel(
    *,
    beleidsregel_in: schemas.BeleidsregelCreate,
    crud_beleidsregel: CRUDBeleidsregel = Depends(deps.get_crud_beleidsregel),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new beleidsregels lineage
    """
    beleidsregel = crud_beleidsregel.create(
        obj_in=beleidsregel_in, by_uuid=current_gebruiker.UUID
    )
    return beleidsregel


@router.get("/beleidsregels/{lineage_id}", response_model=List[schemas.Beleidsregel])
def read_beleidsregel_lineage(
    *,
    lineage_id: int,
    crud_beleidsregel: CRUDBeleidsregel = Depends(deps.get_crud_beleidsregel),
) -> Any:
    """
    Gets all the beleidsregels versions by lineage
    """
    beleidsregels = crud_beleidsregel.all(filters=Filters({"ID": lineage_id}))
    if not beleidsregels:
        raise HTTPException(status_code=404, detail="Beleidsregels not found")
    return beleidsregels


@router.patch("/beleidsregels/{lineage_id}", response_model=schemas.Beleidsregel)
def update_beleidsregel(
    *,
    lineage_id: int,
    beleidsregel_in: schemas.BeleidsregelUpdate,
    crud_beleidsregel: CRUDBeleidsregel = Depends(deps.get_crud_beleidsregel),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new beleidsregels to a lineage
    """
    beleidsregel = crud_beleidsregel.get_latest_by_id(id=lineage_id)
    if not beleidsregel:
        raise HTTPException(status_code=404, detail="Beleidsregel not found")
    if beleidsregel.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    beleidsregel = crud_beleidsregel.update(db_obj=beleidsregel, obj_in=beleidsregel_in)
    return beleidsregel


@router.get("/changes/beleidsregels/{old_uuid}/{new_uuid}")
def changes_beleidsregels(
    old_uuid: str,
    new_uuid: str,
    crud_beleidsregel: CRUDBeleidsregel = Depends(deps.get_crud_beleidsregel),
) -> Any:
    """
    Shows the changes between two versions of beleidsregels.
    """
    try:
        old = crud_beleidsregel.get(old_uuid)
        new = crud_beleidsregel.get(new_uuid)
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
    crud_beleidsregel: CRUDBeleidsregel = Depends(deps.get_crud_beleidsregel),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsregels lineages and shows the latests valid object for each.
    """
    beleidsregels = crud_beleidsregel.valid(offset=offset, limit=limit, filters=filters)
    return beleidsregels


@router.get(
    "/valid/beleidsregels/{lineage_id}", response_model=List[schemas.Beleidsregel]
)
def read_valid_beleidsregel_lineage(
    lineage_id: int,
    crud_beleidsregel: CRUDBeleidsregel = Depends(deps.get_crud_beleidsregel),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsregels in this lineage that are valid
    """
    beleidsregels = crud_beleidsregel.valid(
        ID=lineage_id, offset=offset, limit=limit, filters=filters
    )
    return beleidsregels
