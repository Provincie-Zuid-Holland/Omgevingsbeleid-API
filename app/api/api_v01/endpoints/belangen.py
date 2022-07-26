
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models.gebruiker import GebruikersRol
from app.schemas.filters import Filters
from app.util.compare import Comparator

router = APIRouter()

defer_attributes = {"Omschrijving"}


@router.get(
    "/belangen",
    response_model=List[schemas.Belang],
    response_model_exclude=defer_attributes,
)
def read_belangen(
    db: Session = Depends(deps.get_db),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the belangen lineages and shows the latests object for each
    """
    belangen = crud.belang.latest(
        all=True, filters=filters, offset=offset, limit=limit 
    )

    return belangen


@router.post("/belangen", response_model=schemas.Belang)
def create_belang(
    *,
    db: Session = Depends(deps.get_db),
    belang_in: schemas.BelangCreate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new belangen lineage
    """
    belang = crud.belang.create(
        obj_in=belang_in, by_uuid=current_gebruiker.UUID
    )
    return belang


@router.get("/belangen/{lineage_id}", response_model=List[schemas.Belang])
def read_belang_lineage(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the belangen versions by lineage
    """
    belangen = crud.belang.all(ID=lineage_id)
    if not belangen:
        raise HTTPException(status_code=404, detail="Belangs not found")
    return belangen


@router.patch("/belangen/{lineage_id}", response_model=schemas.Belang)
def update_belang(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    belang_in: schemas.BelangUpdate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new belangen to a lineage
    """
    belang = crud.belang.get_latest_by_id(id=lineage_id)
    if not belang:
        raise HTTPException(status_code=404, detail="Belang not found")
    if belang.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    belang = crud.belang.update(db_obj=belang, obj_in=belang_in)
    return belang


@router.get("/changes/belangen/{old_uuid}/{new_uuid}")
def changes_belangen(
    old_uuid: str,
    new_uuid: str,
) -> Any:
    """
    Shows the changes between two versions of belangen.
    """
    try:
        old = crud.belang.get(old_uuid)
        new = crud.belang.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )

    c = Comparator(schemas.Belang, old, new)
    json_data = jsonable_encoder({"old": old, "changes": c.compare_objects()})

    return JSONResponse(content=json_data)


@router.get(
    "/valid/belangen",
    response_model=List[schemas.Belang],
    response_model_exclude=defer_attributes,
)
def read_valid_belangen(
    db: Session = Depends(deps.get_db),
    offset: int = 0,
    limit: int = 20,
    all_filters: str = "",
    any_filters: str = "",
) -> Any:
    """
    Gets all the belangen lineages and shows the latests valid object for each.
    """
    belangen = crud.belang.valid(
        offset=offset, limit=limit, criteria=parse_filter_str(all_filters)
    )
    return belangen


@router.get(
    "/valid/belangen/{lineage_id}", response_model=List[schemas.Belang]
)
def read_valid_belang_lineage(
    lineage_id: int,
    offset: int = 0,
    limit: int = 20,
    all_filters: str = "",
    any_filters: str = "",
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Gets all the belangen in this lineage that are valid
    """
    belangen = crud.belang.valid(ID=lineage_id, offset=offset, limit=limit)
    return belangen
