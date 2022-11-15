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
    "/verordeningstructuren",
    response_model=List[schemas.Verordeningstructuur],
    response_model_exclude=defer_attributes,
)
def read_verordeningstructuurs(
    db: Session = Depends(deps.get_db),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the verordeningstructuurs lineages and shows the latests object for each
    """
    verordeningstructuurs = crud.verordeningstructuur.latest(
        all=True, filters=filters, offset=offset, limit=limit
    )

    return verordeningstructuurs


@router.post("/verordeningstructuren", response_model=schemas.Verordeningstructuur)
def create_verordeningstructuur(
    *,
    db: Session = Depends(deps.get_db),
    verordeningstructuur_in: schemas.VerordeningstructuurCreate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new verordeningstructuurs lineage
    """
    verordeningstructuur = crud.verordeningstructuur.create(
        obj_in=verordeningstructuur_in, by_uuid=current_gebruiker.UUID
    )
    return verordeningstructuur


@router.get(
    "/verordeningstructuren/{lineage_id}",
    response_model=List[schemas.Verordeningstructuur],
)
def read_verordeningstructuur_lineage(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the verordeningstructuurs versions by lineage
    """
    verordeningstructuurs = crud.verordeningstructuur.all(
        filters=Filters({"ID": lineage_id})
    )
    if not verordeningstructuurs:
        raise HTTPException(status_code=404, detail="Verordeningstructuurs not found")
    return verordeningstructuurs


@router.patch(
    "/verordeningstructuren/{lineage_id}", response_model=schemas.Verordeningstructuur
)
def update_verordeningstructuur(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    verordeningstructuur_in: schemas.VerordeningstructuurUpdate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new verordeningstructuurs to a lineage
    """
    verordeningstructuur = crud.verordeningstructuur.get_latest_by_id(id=lineage_id)
    if not verordeningstructuur:
        raise HTTPException(status_code=404, detail="Verordeningstructuur not found")
    if verordeningstructuur.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    verordeningstructuur = crud.verordeningstructuur.update(
        db_obj=verordeningstructuur,
        obj_in=verordeningstructuur_in,
        by_uuid=current_gebruiker.UUID,
    )
    return verordeningstructuur


@router.get("/changes/verordeningstructuren/{old_uuid}/{new_uuid}")
def changes_verordeningstructuurs(
    old_uuid: str,
    new_uuid: str,
) -> Any:
    """
    Shows the changes between two versions of verordeningstructuurs.
    """
    try:
        old = crud.verordeningstructuur.get(old_uuid)
        new = crud.verordeningstructuur.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )

    json_data = Comparator(
        schema=schemas.Verordeningstructuur, old=old, new=new
    ).get_json_result()
    return JSONResponse(content=json_data)


@router.get(
    "/valid/verordeningstructuren",
    response_model=List[schemas.Verordeningstructuur],
    response_model_exclude=defer_attributes,
)
def read_valid_verordeningstructuurs(
    db: Session = Depends(deps.get_db),
    offset: int = 0,
    limit: int = 20,
    all_filters: str = "",
    any_filters: str = "",
) -> Any:
    """
    Gets all the verordeningstructuurs lineages and shows the latests valid object for each.
    """
    verordeningstructuurs = crud.verordeningstructuur.valid(
        offset=offset, limit=limit, criteria=parse_filter_str(all_filters)
    )
    return verordeningstructuurs


@router.get(
    "/valid/verordeningstructuren/{lineage_id}",
    response_model=List[schemas.Verordeningstructuur],
)
def read_valid_verordeningstructuur_lineage(
    lineage_id: int,
    offset: int = 0,
    limit: int = 20,
    all_filters: str = "",
    any_filters: str = "",
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Gets all the verordeningstructuurs in this lineage that are valid
    """
    verordeningstructuurs = crud.verordeningstructuur.valid(
        ID=lineage_id, offset=offset, limit=limit
    )
    return verordeningstructuurs
