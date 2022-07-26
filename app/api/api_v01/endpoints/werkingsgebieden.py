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
    "/werkingsgebieden",
    response_model=List[schemas.Werkingsgebied],
    response_model_exclude=defer_attributes,
)
def read_werkingsgebied(
    db: Session = Depends(deps.get_db),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the werkingsgebied lineages and shows the latests object for each
    """
    werkingsgebied = crud.beleidsprestatie.latest(
        all=True, filters=filters, offset=offset, limit=limit 
    )

    return werkingsgebied


@router.post("/werkingsgebieden", response_model=schemas.Werkingsgebied)
def create_beleidsprestatie(
    *,
    db: Session = Depends(deps.get_db),
    beleidsprestatie_in: schemas.WerkingsgebiedCreate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new werkingsgebied lineage
    """
    beleidsprestatie = crud.beleidsprestatie.create(
        obj_in=beleidsprestatie_in, by_uuid=current_gebruiker.UUID
    )
    return beleidsprestatie


@router.get("/werkingsgebieden/{lineage_id}", response_model=List[schemas.Werkingsgebied])
def read_beleidsprestatie_lineage(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the werkingsgebied versions by lineage
    """
    werkingsgebied = crud.beleidsprestatie.all(ID=lineage_id)
    if not werkingsgebied:
        raise HTTPException(status_code=404, detail="werkingsgebied not found")
    return werkingsgebied


@router.patch("/werkingsgebieden/{lineage_id}", response_model=schemas.Werkingsgebied)
def update_beleidsprestatie(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    beleidsprestatie_in: schemas.WerkingsgebiedUpdate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new werkingsgebied to a lineage
    """
    beleidsprestatie = crud.beleidsprestatie.get_latest_by_id(id=lineage_id)
    if not beleidsprestatie:
        raise HTTPException(status_code=404, detail="Werkingsgebied not found")
    if beleidsprestatie.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    beleidsprestatie = crud.beleidsprestatie.update(db_obj=beleidsprestatie, obj_in=beleidsprestatie_in)
    return beleidsprestatie


@router.get("/changes/werkingsgebieden/{old_uuid}/{new_uuid}")
def changes_werkingsgebied(
    old_uuid: str,
    new_uuid: str,
) -> Any:
    """
    Shows the changes between two versions of werkingsgebied.
    """
    try:
        old = crud.beleidsprestatie.get(old_uuid)
        new = crud.beleidsprestatie.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )

    c = Comparator(schemas.Werkingsgebied, old, new)
    json_data = jsonable_encoder({"old": old, "changes": c.compare_objects()})

    return JSONResponse(content=json_data)


@router.get(
    "/valid/werkingsgebieden",
    response_model=List[schemas.Werkingsgebied],
    response_model_exclude=defer_attributes,
)
def read_valid_werkingsgebied(
    db: Session = Depends(deps.get_db),
    offset: int = 0,
    limit: int = 20,
    all_filters: str = "",
    any_filters: str = "",
) -> Any:
    """
    Gets all the werkingsgebied lineages and shows the latests valid object for each.
    """
    werkingsgebied = crud.beleidsprestatie.valid(
        offset=offset, limit=limit, criteria=parse_filter_str(all_filters)
    )
    return werkingsgebied


@router.get(
    "/valid/werkingsgebieden/{lineage_id}", response_model=List[schemas.Werkingsgebied]
)
def read_valid_beleidsprestatie_lineage(
    lineage_id: int,
    offset: int = 0,
    limit: int = 20,
    all_filters: str = "",
    any_filters: str = "",
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Gets all the werkingsgebied in this lineage that are valid
    """
    werkingsgebied = crud.beleidsprestatie.valid(ID=lineage_id, offset=offset, limit=limit)
    return werkingsgebied
