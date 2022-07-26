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
    "/beleidskeuzes",
    response_model=List[schemas.Beleidskeuze],
    response_model_exclude=defer_attributes,
)
def read_beleidskeuzes(
    db: Session = Depends(deps.get_db),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidskeuzes lineages and shows the latests object for each
    """
    beleidskeuzes = crud.beleidskeuze.latest(
        all=True, filters=filters, offset=offset, limit=limit
    )

    return beleidskeuzes


@router.post("/beleidskeuzes", response_model=schemas.Beleidskeuze)
def create_beleidskeuze(
    *,
    db: Session = Depends(deps.get_db),
    beleidskeuze_in: schemas.BeleidskeuzeCreate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new beleidskeuzes lineage
    """
    beleidskeuze = crud.beleidskeuze.create(
        obj_in=beleidskeuze_in, by_uuid=current_gebruiker.UUID
    )
    return beleidskeuze


@router.get("/beleidskeuzes/{lineage_id}", response_model=List[schemas.Beleidskeuze])
def read_beleidskeuze_lineage(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the beleidskeuzes versions by lineage
    """
    beleidskeuzes = crud.beleidskeuze.all(ID=lineage_id)
    if not beleidskeuzes:
        raise HTTPException(status_code=404, detail="Beleidskeuzes not found")
    return beleidskeuzes


@router.patch("/beleidskeuzes/{lineage_id}", response_model=schemas.Beleidskeuze)
def update_beleidskeuze(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    beleidskeuze_in: schemas.BeleidskeuzeUpdate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new beleidskeuzes to a lineage
    """
    beleidskeuze = crud.beleidskeuze.get_latest_by_id(id=lineage_id)
    if not beleidskeuze:
        raise HTTPException(status_code=404, detail="Beleidskeuze not found")
    if beleidskeuze.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    beleidskeuze = crud.beleidskeuze.update(db_obj=beleidskeuze, obj_in=beleidskeuze_in)
    return beleidskeuze


@router.get("/changes/beleidskeuzes/{old_uuid}/{new_uuid}")
def changes_beleidskeuzes(
    old_uuid: str,
    new_uuid: str,
) -> Any:
    """
    Shows the changes between two versions of beleidskeuzes.
    """
    try:
        old = crud.beleidskeuze.get(old_uuid)
        new = crud.beleidskeuze.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )

    c = Comparator(schemas.Beleidskeuze, old, new)
    # print(c.fields)
    json_data = jsonable_encoder({"old": old, "changes": c.compare_objects()})

    return JSONResponse(content=json_data)


@router.get(
    "/valid/beleidskeuzes",
    response_model=List[schemas.Beleidskeuze],
    response_model_exclude=defer_attributes,
)
def read_valid_beleidskeuzes(
    db: Session = Depends(deps.get_db),
    offset: int = 0,
    limit: int = 20,
    all_filters: str = "",
    any_filters: str = "",
) -> Any:
    """
    Gets all the beleidskeuzes lineages and shows the latests valid object for each.
    """
    beleidskeuzes = crud.beleidskeuze.valid(
        offset=offset, limit=limit, criteria=parse_filter_str(all_filters)
    )
    return beleidskeuzes


@router.get(
    "/valid/beleidskeuzes/{lineage_id}", response_model=List[schemas.Beleidskeuze]
)
def read_valid_beleidskeuze_lineage(
    lineage_id: int,
    offset: int = 0,
    limit: int = 20,
    all_filters: str = "",
    any_filters: str = "",
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Gets all the beleidskeuzes in this lineage that are valid
    """
    beleidskeuzes = crud.beleidskeuze.valid(ID=lineage_id, offset=offset, limit=limit)
    return beleidskeuzes
