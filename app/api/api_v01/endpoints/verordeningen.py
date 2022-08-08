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

defer_attributes = {"Inhoud"}


@router.get(
    "/verordeningen",
    response_model=List[schemas.Verordening],
    response_model_exclude=defer_attributes,
)
def read_verordening(
    db: Session = Depends(deps.get_db),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the verordening lineages and shows the latests object for each
    """
    verordening = crud.verordening.latest(
        all=True, filters=filters, offset=offset, limit=limit
    )

    return verordening


@router.post("/verordeningen", response_model=schemas.Verordening)
def create_verordening(
    *,
    db: Session = Depends(deps.get_db),
    verordening_in: schemas.VerordeningCreate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new verordening lineage
    """
    verordening = crud.verordening.create(
        obj_in=verordening_in, by_uuid=current_gebruiker.UUID
    )
    return verordening


@router.get("/verordeningen/{lineage_id}", response_model=List[schemas.Verordening])
def read_verordening_lineage(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the verordening versions by lineage
    """
    verordening = crud.verordening.all(filters=Filters({"ID": lineage_id}))
    if not verordening:
        raise HTTPException(status_code=404, detail="verordening not found")
    return verordening


@router.patch("/verordeningen/{lineage_id}", response_model=schemas.Verordening)
def update_verordening(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    verordening_in: schemas.VerordeningUpdate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new verordening to a lineage
    """
    verordening = crud.verordening.get_latest_by_id(id=lineage_id)
    if not verordening:
        raise HTTPException(status_code=404, detail="Verordening not found")
    if verordening.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    verordening = crud.verordening.update(db_obj=verordening, obj_in=verordening_in)
    return verordening


@router.get("/changes/verordeningen/{old_uuid}/{new_uuid}")
def changes_verordening(
    old_uuid: str,
    new_uuid: str,
) -> Any:
    """
    Shows the changes between two versions of verordening.
    """
    try:
        old = crud.verordening.get(old_uuid)
        new = crud.verordening.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )

    json_data = Comparator(
        schema=schemas.Verordening, old=old, new=new
    ).get_json_result()
    return JSONResponse(content=json_data)


@router.get(
    "/valid/verordeningen",
    response_model=List[schemas.Verordening],
    response_model_exclude=defer_attributes,
)
def read_valid_verordening(
    db: Session = Depends(deps.get_db),
    offset: int = 0,
    limit: int = 20,
    filters: Filters = Depends(deps.string_filters),
) -> Any:
    """
    Gets all the verordening lineages and shows the latests valid object for each.
    """
    verordening = crud.verordening.valid(offset=offset, limit=limit, filters=filters)
    return verordening


@router.get(
    "/valid/verordeningen/{lineage_id}", response_model=List[schemas.Verordening]
)
def read_valid_verordening_lineage(
    lineage_id: int,
    offset: int = 0,
    limit: int = 20,
    filters: Filters = Depends(deps.string_filters),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Gets all the verordening in this lineage that are valid
    """
    verordening = crud.verordening.valid(
        ID=lineage_id, offset=offset, limit=limit, filters=filters
    )
    return verordening
